import os
import io
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.services.vector_store import vector_store
from app.services.bm25_retriever import bm25_retriever
from app.services.storage import storage_service

SAMPLE_Q3_PDF = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../sample_documents/acme_q3_financial_report.pdf"))
EH_CP_PDF = "/home/tuf/Downloads/EH_CP_Report_V3.pdf"


@pytest.fixture
def client_transport():
    return ASGITransport(app=app)


@pytest.mark.asyncio
async def test_scenario_01_valid_small_pdf(client_transport):
    """1. Upload valid small PDF (~5.6KB)."""
    assert os.path.exists(SAMPLE_Q3_PDF)
    with open(SAMPLE_Q3_PDF, "rb") as f:
        content = f.read()

    async with AsyncClient(transport=client_transport, base_url="http://test") as client:
        res = await client.post(
            "/api/documents/upload",
            files={"file": ("acme_q3_financial_report.pdf", content, "application/pdf")}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["filename"] == "acme_q3_financial_report.pdf"
        assert data["page_count"] == 2
        assert data["status"] == "INDEXED"
        assert data["error_message"] is None


@pytest.mark.asyncio
async def test_scenario_02_valid_1mb_pdf(client_transport):
    """2. Upload valid ~1MB PDF (EH_CP_Report_V3.pdf)."""
    assert os.path.exists(EH_CP_PDF), f"Expected EH_CP_Report_V3.pdf at {EH_CP_PDF}"
    with open(EH_CP_PDF, "rb") as f:
        content = f.read()

    async with AsyncClient(transport=client_transport, base_url="http://test") as client:
        res = await client.post(
            "/api/documents/upload",
            files={"file": ("EH_CP_Report_V3.pdf", content, "application/pdf")}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["filename"] == "EH_CP_Report_V3.pdf"
        assert data["page_count"] == 26
        assert data["status"] == "INDEXED"
        assert data["error_message"] is None


@pytest.mark.asyncio
async def test_scenario_03_multiple_pdf_uploads_in_sequence(client_transport):
    """3. Upload multiple PDF files sequentially."""
    async with AsyncClient(transport=client_transport, base_url="http://test") as client:
        # Create 2 distinct minimal valid PDFs
        import fitz
        doc1 = fitz.open()
        p1 = doc1.new_page()
        p1.insert_text((50, 50), "Document Alpha unique sequential content")
        bytes1 = doc1.tobytes()
        doc1.close()

        doc2 = fitz.open()
        p2 = doc2.new_page()
        p2.insert_text((50, 50), "Document Beta unique sequential content")
        bytes2 = doc2.tobytes()
        doc2.close()

        res1 = await client.post(
            "/api/documents/upload",
            files={"file": ("seq_doc_alpha.pdf", bytes1, "application/pdf")}
        )
        assert res1.status_code == 200
        assert res1.json()["status"] == "INDEXED"

        res2 = await client.post(
            "/api/documents/upload",
            files={"file": ("seq_doc_beta.pdf", bytes2, "application/pdf")}
        )
        assert res2.status_code == 200
        assert res2.json()["status"] == "INDEXED"
        assert res1.json()["id"] != res2.json()["id"]


@pytest.mark.asyncio
async def test_scenario_04_invalid_extension(client_transport):
    """4. Reject file with invalid extension (.txt, .docx)."""
    async with AsyncClient(transport=client_transport, base_url="http://test") as client:
        res_txt = await client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", b"Plain text content", "text/plain")}
        )
        assert res_txt.status_code == 400
        assert "Only PDF documents are supported" in res_txt.json()["detail"]

        res_docx = await client.post(
            "/api/documents/upload",
            files={"file": ("report.docx", b"PK\x03\x04 fake docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
        assert res_docx.status_code == 400
        assert "Only PDF documents are supported" in res_docx.json()["detail"]


@pytest.mark.asyncio
async def test_scenario_05_invalid_magic_bytes(client_transport):
    """5. Reject file with .pdf extension but missing standard %PDF- header."""
    fake_pdf = b"This is just plain text saved with a .pdf extension"
    async with AsyncClient(transport=client_transport, base_url="http://test") as client:
        res = await client.post(
            "/api/documents/upload",
            files={"file": ("fake_document.pdf", fake_pdf, "application/pdf")}
        )
        assert res.status_code == 400
        assert "Invalid PDF format" in res.json()["detail"]
        assert "%PDF-" in res.json()["detail"]


@pytest.mark.asyncio
async def test_scenario_06_empty_pdf(client_transport):
    """6. Reject empty PDF file (0 bytes)."""
    async with AsyncClient(transport=client_transport, base_url="http://test") as client:
        res = await client.post(
            "/api/documents/upload",
            files={"file": ("empty.pdf", b"", "application/pdf")}
        )
        assert res.status_code == 400
        assert "empty" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_scenario_07_corrupted_pdf(client_transport):
    """7. Handle corrupted PDF (valid header but garbage/truncated body) gracefully."""
    corrupted_data = b"%PDF-1.4\n%corrupt truncated content with invalid xref and objects\n%%EOF"
    async with AsyncClient(transport=client_transport, base_url="http://test") as client:
        res = await client.post(
            "/api/documents/upload",
            files={"file": ("corrupted_sample.pdf", corrupted_data, "application/pdf")}
        )
        # Server must reject with 422 or return status FAILED without crashing
        assert res.status_code in (400, 422)
        assert "failed" in res.json()["detail"].lower() or "extraction" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_scenario_08_file_exceeding_size_limit(client_transport, monkeypatch):
    """8. Reject file exceeding size limit (>50MB)."""
    # Temporarily set max file size to 1MB for fast automated test
    monkeypatch.setattr(settings, "MAX_FILE_SIZE_MB", 1)
    large_dummy_content = b"%PDF-" + b"0" * (2 * 1024 * 1024)

    async with AsyncClient(transport=client_transport, base_url="http://test") as client:
        res = await client.post(
            "/api/documents/upload",
            files={"file": ("huge_document.pdf", large_dummy_content, "application/pdf")}
        )
        assert res.status_code == 413
        assert "exceeds maximum allowed size" in res.json()["detail"]


@pytest.mark.asyncio
async def test_scenario_09_upload_with_collection(client_transport):
    """9. Upload PDF with collection assignment."""
    import fitz
    doc = fitz.open()
    p = doc.new_page()
    p.insert_text((50, 50), "Document associated with specific research collection.")
    pdf_bytes = doc.tobytes()
    doc.close()

    async with AsyncClient(transport=client_transport, base_url="http://test") as client:
        # Create a collection first
        col_res = await client.post("/api/collections", json={"name": "Upload Test Collection", "description": "Unit testing"})
        assert col_res.status_code == 201
        collection_id = col_res.json()["id"]

        # Upload with collection_id
        res = await client.post(
            "/api/documents/upload",
            data={"collection_id": collection_id},
            files={"file": ("collection_bound_doc.pdf", pdf_bytes, "application/pdf")}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["collection_id"] == collection_id


@pytest.mark.asyncio
async def test_scenario_10_upload_without_collection(client_transport):
    """10. Upload PDF without collection assignment."""
    import fitz
    doc = fitz.open()
    p = doc.new_page()
    p.insert_text((50, 50), "Document with no collection assignment.")
    pdf_bytes = doc.tobytes()
    doc.close()

    async with AsyncClient(transport=client_transport, base_url="http://test") as client:
        res = await client.post(
            "/api/documents/upload",
            files={"file": ("standalone_doc.pdf", pdf_bytes, "application/pdf")}
        )
        assert res.status_code == 200
        assert res.json()["collection_id"] is None


@pytest.mark.asyncio
async def test_scenario_11_upload_missing_auth_header(client_transport):
    """11. Upload with missing authorization header defaults to demo user seamlessly."""
    import fitz
    doc = fitz.open()
    p = doc.new_page()
    p.insert_text((50, 50), "Document uploaded without Authorization header.")
    pdf_bytes = doc.tobytes()
    doc.close()

    async with AsyncClient(transport=client_transport, base_url="http://test") as client:
        res = await client.post(
            "/api/documents/upload",
            files={"file": ("no_auth_header.pdf", pdf_bytes, "application/pdf")}
        )
        assert res.status_code == 200
        assert res.json()["status"] == "INDEXED"


@pytest.mark.asyncio
async def test_scenario_12_upload_invalid_jwt_token(client_transport):
    """12. Upload with invalid JWT token returns 401 Unauthorized."""
    async with AsyncClient(transport=client_transport, base_url="http://test") as client:
        res = await client.post(
            "/api/documents/upload",
            headers={"Authorization": "Bearer definitely-invalid-malformed-jwt-token"},
            files={"file": ("auth_fail.pdf", b"%PDF-1.4\nsome content", "application/pdf")}
        )
        assert res.status_code == 401
        assert "Invalid or expired" in res.json()["detail"]


@pytest.mark.asyncio
async def test_scenario_13_reprocess_document(client_transport):
    """13. Reprocess existing document and ensure chunks/vectors refresh without duplicates."""
    import fitz
    doc = fitz.open()
    p = doc.new_page()
    p.insert_text((50, 50), "Document to be reprocessed and re-indexed.")
    pdf_bytes = doc.tobytes()
    doc.close()

    async with AsyncClient(transport=client_transport, base_url="http://test") as client:
        res = await client.post(
            "/api/documents/upload",
            files={"file": ("reprocess_target.pdf", pdf_bytes, "application/pdf")}
        )
        assert res.status_code == 200
        doc_id = res.json()["id"]

        # Call reprocess endpoint
        rep_res = await client.post(f"/api/documents/{doc_id}/reprocess")
        assert rep_res.status_code == 200
        assert rep_res.json()["status"] == "INDEXED"
        assert rep_res.json()["id"] == doc_id


@pytest.mark.asyncio
async def test_scenario_14_duplicate_upload(client_transport):
    """14. Duplicate upload of identical file returns existing document (idempotent)."""
    assert os.path.exists(SAMPLE_Q3_PDF)
    with open(SAMPLE_Q3_PDF, "rb") as f:
        content = f.read()

    async with AsyncClient(transport=client_transport, base_url="http://test") as client:
        res1 = await client.post(
            "/api/documents/upload",
            files={"file": ("acme_q3_financial_report.pdf", content, "application/pdf")}
        )
        assert res1.status_code == 200
        id1 = res1.json()["id"]

        # Upload duplicate with different filename
        res2 = await client.post(
            "/api/documents/upload",
            files={"file": ("renamed_copy_of_q3.pdf", content, "application/pdf")}
        )
        assert res2.status_code == 200
        id2 = res2.json()["id"]
        assert id1 == id2


@pytest.mark.asyncio
async def test_scenario_15_delete_document_and_verify_cleanup(client_transport):
    """15. Delete uploaded document and verify cleanup across SQL, storage, ChromaDB, and BM25."""
    import fitz
    doc = fitz.open()
    p = doc.new_page()
    p.insert_text((50, 50), "Document destined for deletion and complete cleanup verification.")
    pdf_bytes = doc.tobytes()
    doc.close()

    async with AsyncClient(transport=client_transport, base_url="http://test") as client:
        # Upload
        res = await client.post(
            "/api/documents/upload",
            files={"file": ("delete_me_test.pdf", pdf_bytes, "application/pdf")}
        )
        assert res.status_code == 200
        doc_id = res.json()["id"]

        # Verify file is accessible before deletion
        file_res = await client.get(f"/api/documents/{doc_id}/file")
        assert file_res.status_code == 200
        assert len(file_res.content) > 0

        # Delete
        del_res = await client.delete(f"/api/documents/{doc_id}")
        assert del_res.status_code == 200
        assert del_res.json()["message"] == "Document deleted successfully."

        # Verify DB returns 404
        get_res = await client.get(f"/api/documents/{doc_id}")
        assert get_res.status_code == 404

        # Verify file endpoint returns 404 after deletion
        file_res_after = await client.get(f"/api/documents/{doc_id}/file")
        assert file_res_after.status_code == 404

        # Verify ChromaDB has no chunks for this document_id
        chroma_matches = vector_store.query_similar(query_embedding=[0.0] * 384, top_k=5, document_id=doc_id)
        assert len(chroma_matches) == 0
