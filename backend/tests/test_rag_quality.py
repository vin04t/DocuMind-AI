import pytest
import re
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import DocumentChunk
from app.services.rag_engine import rag_engine
from app.services.bm25_retriever import bm25_retriever


async def _init_bm25(db):
    """Ensure in-memory BM25 index is populated from the test database."""
    res = await db.execute(select(DocumentChunk))
    db_chunks = res.scalars().all()
    chunks_data = [
        {
            "id": c.id,
            "document_id": c.document_id,
            "page_number": c.page_number,
            "content": c.content,
        }
        for c in db_chunks
    ]
    bm25_retriever.index_chunks(chunks_data)


@pytest.mark.asyncio
async def test_regression_keyboard_shortcut_question():
    """
    Regression Test 1: Keyboard Shortcut Questions
    Verifies:
    - User query 'what is key for new windows' returns concise 1-sentence answer.
    - Direct shortcut key (Ctrl+Shift+N) is prioritized.
    - No 30+ shortcut text dump.
    - Valid citation to keyboard-shortcuts-linux.pdf.
    """
    async with AsyncSessionLocal() as db:
        await _init_bm25(db)
        res = await rag_engine.process_question(db, "what is key for new windows")
        
        answer = res["answer"]
        assert not res["is_unanswerable"], "Shortcut query should be answered"
        assert "Ctrl+Shift+N" in answer or "ctrl+shift+n" in answer.lower(), f"Expected Ctrl+Shift+N in answer, got: {answer}"
        assert "window" in answer.lower(), f"Expected window in answer, got: {answer}"
        
        # Verify concise generation (should not dump 30 shortcuts)
        assert len(answer.split()) < 40, f"Expected concise answer (< 40 words), got {len(answer.split())} words: {answer}"
        assert "Close All" not in answer, "Unrelated shortcuts must not be dumped"
        assert "Toggle breakpoint" not in answer, "Unrelated shortcuts must not be dumped"
        
        # Check citation
        assert len(res["citations"]) >= 1
        assert any("keyboard-shortcuts-linux.pdf" in c.get("document_name", "") for c in res["citations"])
        
        # Check claim verification
        if res.get("verification_claims"):
            supported = [c for c in res["verification_claims"] if c.get("status") == "SUPPORTED" or c.get("verification_status") == "SUPPORTED"]
            assert len(supported) >= 1, "Shortcut claim must be verified as SUPPORTED"


@pytest.mark.asyncio
async def test_regression_simple_factual_question():
    """
    Regression Test 2: Simple Factual Questions
    Verifies:
    - Answer is concise (1–3 sentences).
    - Direct factual answer is prioritized in the first sentence.
    - Valid inline citation present.
    """
    async with AsyncSessionLocal() as db:
        await _init_bm25(db)
        res = await rag_engine.process_question(db, "What was Acme Technologies' total revenue in Q3 2024?")
        
        answer = res["answer"]
        assert not res["is_unanswerable"]
        assert "42.5" in answer or "$42.5M" in answer or "42.5 million" in answer
        
        # Verify 1-3 sentences
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', answer) if s.strip()]
        assert 1 <= len(sentences) <= 3, f"Expected 1-3 sentences, got {len(sentences)}: {answer}"
        
        # Verify first sentence has the direct answer
        first_sent = sentences[0]
        assert "42.5" in first_sent, f"Direct answer must appear in the first sentence: {first_sent}"
        
        # Verify citations
        assert any("acme_q3_financial_report.pdf" in c.get("document_name", "") for c in res["citations"])


@pytest.mark.asyncio
async def test_regression_ambiguous_question_handling():
    """
    Regression Test 3: Ambiguous Questions
    Verifies:
    - Queries with materially different versions/policies across years prompt a clarification.
    - Both policy values (2023: $1,200 and 2024: $800) are explicitly reported.
    - Both documents are cited.
    """
    async with AsyncSessionLocal() as db:
        await _init_bm25(db)
        res = await rag_engine.process_question(db, "What is the annual home office stipend?")
        
        answer = res["answer"]
        assert not res["is_unanswerable"]
        
        # Both policy figures must be present
        assert "1,200" in answer or "1200" in answer, f"Expected 2023 stipend ($1,200) in answer: {answer}"
        assert "800" in answer, f"Expected 2024 stipend ($800) in answer: {answer}"
        
        # Clarification prompt must be present
        clarification_markers = ["clarify", "which policy", "which year", "depends on"]
        assert any(m in answer.lower() for m in clarification_markers), f"Expected clarification prompt in answer: {answer}"
        
        # Citations must cover both policy documents
        cited_docs = {c.get("document_name", "") for c in res["citations"]}
        assert any("2023" in d for d in cited_docs), f"Expected 2023 policy citation: {cited_docs}"
        assert any("2024" in d for d in cited_docs), f"Expected 2024 policy citation: {cited_docs}"


@pytest.mark.asyncio
async def test_regression_single_sentence_in_large_document():
    """
    Regression Test 4: Questions whose answers appear in only one sentence of a large document
    Verifies:
    - Extracts the single exact fact without dumping surrounding paragraphs.
    - Answer is 1-2 concise sentences.
    """
    async with AsyncSessionLocal() as db:
        await _init_bm25(db)
        # Question about specific model from technical whitepaper
        res = await rag_engine.process_question(
            db, "Which cross-encoder reranker model is recommended in the technical whitepaper for top-K reranking?"
        )
        
        answer = res["answer"]
        assert not res["is_unanswerable"]
        assert "ms-marco-MiniLM-L-6-v2" in answer, f"Expected reranker model in answer: {answer}"
        
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', answer) if s.strip()]
        assert 1 <= len(sentences) <= 2, f"Expected 1-2 sentences, got {len(sentences)}: {answer}"
        assert len(answer.split()) < 60, f"Expected concise answer, got {len(answer.split())} words"


@pytest.mark.asyncio
async def test_regression_multi_document_comparison():
    """
    Regression Test 5: Multi-Document Questions
    Verifies:
    - Accurately aggregates/compares facts across multiple documents.
    - Citations reflect both source documents.
    """
    async with AsyncSessionLocal() as db:
        await _init_bm25(db)
        res = await rag_engine.process_question(db, "Compare total headcount at Acme between Q3 2024 and Q4 2024.")
        
        answer = res["answer"]
        assert not res["is_unanswerable"]
        assert "480" in answer, f"Expected Q3 headcount 480 in answer: {answer}"
        assert "520" in answer, f"Expected Q4 headcount 520 in answer: {answer}"
        
        # Both financial reports should be cited
        cited_docs = {c.get("document_name", "") for c in res["citations"]}
        assert any("q3" in d.lower() for d in cited_docs), f"Expected Q3 report in citations: {cited_docs}"
        assert any("q4" in d.lower() for d in cited_docs), f"Expected Q4 report in citations: {cited_docs}"


@pytest.mark.asyncio
async def test_regression_unanswerable_question_abstention():
    """
    Regression Test 6: Unanswerable Questions
    Verifies:
    - Properly abstains when information is absent from the indexed documents.
    - Declares what information is missing.
    - Does not fabricate answers or return invalid citations.
    """
    async with AsyncSessionLocal() as db:
        await _init_bm25(db)
        res = await rag_engine.process_question(
            db, "What dental insurance benefits does Acme provide to remote employees?"
        )
        
        assert res["is_unanswerable"] is True
        answer = res["answer"].lower()
        assert "cannot be established" in answer or "missing information" in answer
        assert len(res["citations"]) == 0, f"Unanswerable question should have 0 citations, got {len(res['citations'])}"


@pytest.mark.asyncio
async def test_regression_citation_deduplication():
    """
    Regression Test 7: Citation Deduplication
    Verifies:
    - No two citations share identical (document_name, page_number).
    - Slices with multiple chunks from the same page produce only one unique citation for that page.
    """
    async with AsyncSessionLocal() as db:
        await _init_bm25(db)
        # Test with shortcut query where multiple chunks from Page 1 exist
        res = await rag_engine.process_question(db, "what is key for new windows")
        citations = res["citations"]
        
        assert len(citations) >= 1
        seen_pairs = set()
        for c in citations:
            pair = (c.get("document_name"), c.get("page_number"))
            assert pair not in seen_pairs, f"Duplicate citation detected for {pair}!"
            seen_pairs.add(pair)
            
        assert len(citations) == len(seen_pairs), "Every citation must have a unique (document_name, page_number) pair"
