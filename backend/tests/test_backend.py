import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.services.document_processor import document_processor
from app.services.chunker import chunker
from app.services.embedding import embedding_service
from app.services.vector_store import vector_store
from app.services.bm25_retriever import bm25_retriever
from app.services.hybrid_retriever import hybrid_retriever
from app.services.verification_service import verification_service
from app.services.conflict_detector import conflict_detector
from app.services.llm_provider import llm_provider

# Path to sample PDF generated earlier
SAMPLE_PDF = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../sample_documents/acme_q3_financial_report.pdf"))


@pytest.mark.asyncio
async def test_api_health():
    """Verify health endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "DocuMind" in data["service"]


@pytest.mark.asyncio
async def test_pdf_extraction_and_metadata():
    """Verify PDF extraction, page count, and metadata preservation."""
    assert os.path.exists(SAMPLE_PDF), f"Sample PDF missing at {SAMPLE_PDF}"
    result = document_processor.extract_document(SAMPLE_PDF)
    assert result["page_count"] == 2
    assert result["is_scanned"] is False
    assert len(result["pages"]) == 2
    assert "Acme Technologies" in result["pages"][0]["text"]
    assert result["pages"][0]["page_number"] == 1
    assert result["pages"][1]["page_number"] == 2


def test_chunking_and_page_preservation():
    """Verify intelligent text chunking preserves page numbers and character offsets."""
    pages = [
        {"page_number": 1, "text": "Paragraph one discussing revenue of $42.5M.\n\nParagraph two with net income."},
        {"page_number": 2, "text": "Paragraph three on page two regarding CloudScale ARR reaching $15 million."}
    ]
    chunks = chunker.chunk_pages(document_id="doc-test-1", pages=pages)
    assert len(chunks) >= 2
    assert chunks[0]["page_number"] == 1
    assert chunks[-1]["page_number"] == 2
    assert "$42.5M" in chunks[0]["content"]
    assert chunks[0]["start_char"] >= 0
    assert chunks[0]["end_char"] > chunks[0]["start_char"]


def test_embedding_and_dimension():
    """Verify embedding service produces 384-dim normalized vectors."""
    query = "Acme Technologies quarterly revenue"
    vec = embedding_service.embed_query(query)
    assert len(vec) == 384
    # Check vector values are finite floats
    assert all(isinstance(x, float) for x in vec)


def test_bm25_retrieval_and_scoring():
    """Verify BM25 keyword search ranks exact keyword matches highest."""
    test_chunks = [
        {"id": "c1", "content": "Acme Technologies generated $42.5 million in revenue during Q3.", "document_id": "d1", "page_number": 1},
        {"id": "c2", "content": "The weather forecast in Seattle expects rain tomorrow.", "document_id": "d1", "page_number": 1},
        {"id": "c3", "content": "Enterprise customer retention rate held at 94 percent.", "document_id": "d1", "page_number": 2}
    ]
    bm25_retriever.index_chunks(test_chunks, append=False)
    results = bm25_retriever.search("revenue $42.5 million", top_k=2)
    assert len(results) > 0
    assert results[0]["id"] == "c1"
    assert results[0]["bm25_score"] > 0.0


def test_hybrid_retrieval_and_rrf():
    """Verify Reciprocal Rank Fusion combines sparse and dense candidates."""
    # Seed vector store with sample chunks
    test_chunks = [
        {"id": "h1", "content": "CloudScale ARR reached $15 million within six weeks of launch.", "document_id": "d1", "page_number": 2, "chunk_index": 0},
        {"id": "h2", "content": "General corporate guidelines and administrative procedures.", "document_id": "d1", "page_number": 1, "chunk_index": 1}
    ]
    embeddings = embedding_service.embed_texts([c["content"] for c in test_chunks])
    vector_store.add_chunks(test_chunks, embeddings)
    bm25_retriever.index_chunks(test_chunks, append=True)

    hybrid_res = hybrid_retriever.retrieve(query="CloudScale ARR $15 million", top_k=2)
    assert len(hybrid_res["results"]) > 0
    top_match = hybrid_res["results"][0]
    assert top_match["id"] == "h1"
    assert "rrf_score" in top_match
    assert top_match["confidence_score"] > 0.0


@pytest.mark.asyncio
async def test_evidence_verification_claims():
    """Verify claim-level verification distinguishes supported from contradicted/unsupported claims."""
    passages = [
        {
            "document_id": "d1",
            "document_name": "acme_q3_report.pdf",
            "page_number": 1,
            "content": "Total Revenue was $42.5 million, representing a 28% year-over-year increase."
        }
    ]

    # Test SUPPORTED claim
    res_sup = await verification_service.verify_answer_claims(
        answer="Total Revenue was $42.5 million in Q3.",
        evidence_passages=passages,
        claims=["Total Revenue was $42.5 million in Q3."]
    )
    assert len(res_sup) == 1
    assert res_sup[0]["status"] == "SUPPORTED"
    assert res_sup[0]["page_number"] == 1

    # Test CONTRADICTED claim (wrong revenue number for same subject)
    res_con = await verification_service.verify_answer_claims(
        answer="Total Revenue was $99.9 million in Q3.",
        evidence_passages=passages,
        claims=["Total Revenue was $99.9 million in Q3."]
    )
    assert len(res_con) == 1
    assert res_con[0]["status"] in ("CONTRADICTED", "PARTIALLY_SUPPORTED")

    # Test NOT_SUPPORTED claim
    res_not = await verification_service.verify_answer_claims(
        answer="Acme owns sixteen luxury yachts in the Caribbean.",
        evidence_passages=passages,
        claims=["Acme owns sixteen luxury yachts in the Caribbean."]
    )
    assert len(res_not) == 1
    assert res_not[0]["status"] == "NOT_SUPPORTED"


def test_conflict_detection_service():
    """Verify cross-document conflict detection discovers conflicting policy stipends."""
    doc_2023 = {
        "id": "doc_23",
        "filename": "policy_2023.pdf",
        "chunks": [
            {"page_number": 2, "content": "Annual Home Office Stipend: Each eligible remote employee receives an annual stipend of $1,200 per calendar year."}
        ]
    }
    doc_2024 = {
        "id": "doc_24",
        "filename": "policy_2024.pdf",
        "chunks": [
            {"page_number": 2, "content": "Annual Home Office Stipend: Under the 2024 budget guidelines, the annual home office stipend is adjusted to $800 per employee."}
        ]
    }

    conflicts = conflict_detector.detect_conflicts_across_documents([doc_2023, doc_2024])
    assert len(conflicts) >= 1
    stipend_conflict = conflicts[0]
    assert stipend_conflict["conflict_type"] == "policy"
    assert "$1,200" in stipend_conflict["statement_a"] or "$1,200" in stipend_conflict["statement_b"]
    assert "$800" in stipend_conflict["statement_a"] or "$800" in stipend_conflict["statement_b"]
    assert stipend_conflict["review_status"] == "NEEDS_INVESTIGATION"


@pytest.mark.asyncio
async def test_unanswerable_question_abstention():
    """Verify platform abstains gracefully on unanswerable queries."""
    res = await llm_provider.generate_grounded_answer(
        query="What is the CEO's favorite breakfast cereal?",
        evidence_chunks=[],
        confidence_threshold=0.35
    )
    assert res["is_unanswerable"] is True
    assert "cannot be established" in res["answer"].lower()
