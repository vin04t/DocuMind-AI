import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_full_api_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res = await client.get("/api/health")
        assert res.status_code == 200
        health_data = res.json()
        assert health_data["status"] == "healthy"
        assert health_data["database"] == "connected"

        # 2. Document listing
        res = await client.get("/api/documents")
        assert res.status_code == 200
        docs = res.json()
        assert isinstance(docs, list)
        assert len(docs) >= 1
        first_doc = docs[0]
        assert "filename" in first_doc
        assert first_doc["status"] == "INDEXED"

        # 3. Document PDF serving
        res = await client.get(f"/api/documents/{first_doc['id']}/file")
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/pdf"
        assert len(res.content) > 100

        # 4. Collections
        res = await client.get("/api/collections")
        assert res.status_code == 200
        collections = res.json()
        assert isinstance(collections, list)

        # Create a new collection
        res = await client.post("/api/collections", json={
            "name": "E2E Test Collection",
            "description": "Created during automated E2E test"
        })
        assert res.status_code == 201
        created_col = res.json()
        assert created_col["name"] == "E2E Test Collection"

        # 5. Chat Conversation & Question Answering
        res = await client.post("/api/chat/conversations", json={
            "title": "E2E Revenue Investigation"
        })
        assert res.status_code in (200, 201)
        conv = res.json()
        conv_id = conv["id"]
        assert conv_id is not None

        # Send a natural language query
        res = await client.post(f"/api/chat/conversations/{conv_id}/messages", json={
            "content": "What was Acme's total revenue in Q3 2024?"
        })
        assert res.status_code == 200
        asst = res.json()
        assert asst["role"] == "assistant"
        assert len(asst["content"]) > 0
        assert "$42.5" in asst["content"] or "revenue" in asst["content"].lower()
        assert len(asst["citations"]) >= 1
        assert asst["citations"][0]["page_number"] >= 1

        # 6. Ad-hoc Claim Verification
        q3_doc = next((d for d in docs if "q3" in d["filename"].lower()), first_doc)
        res = await client.post("/api/verification/verify-claim", json={
            "claim": "Acme Technologies reported $42.5 million in Q3 revenue.",
            "document_id": q3_doc["id"]
        })
        assert res.status_code == 200
        claim_result = res.json()
        assert claim_result["status"] in ("SUPPORTED", "PARTIALLY_SUPPORTED")
        assert len(claim_result["supporting_passage"]) > 10
        assert claim_result["page_number"] >= 1

        # 7. Verification claims listing
        res = await client.get("/api/verification/claims")
        assert res.status_code == 200
        claims_list = res.json()
        assert isinstance(claims_list, list)

        # 8. Conflict Detection
        res = await client.get("/api/conflicts")
        assert res.status_code == 200
        conflicts = res.json()
        assert isinstance(conflicts, list)
        assert len(conflicts) >= 1
        conflict_id = conflicts[0]["id"]

        # Update conflict status
        res = await client.patch(f"/api/conflicts/{conflict_id}/status", json={
            "review_status": "REVIEWED",
            "resolution_notes": "Verified by automated E2E test."
        })
        assert res.status_code == 200
        updated_conflict = res.json()
        assert updated_conflict["review_status"] == "REVIEWED"

        # 9. Research Analytics
        res = await client.get("/api/analytics/summary")
        assert res.status_code == 200
        analytics = res.json()
        assert "total_documents" in analytics
        assert "total_questions" in analytics
        assert "avg_answer_latency_ms" in analytics
        assert "verification_stats" in analytics
        assert analytics["total_documents"] >= 5

        # 10. Operations Activity Monitor
        res = await client.get("/api/activity")
        assert res.status_code == 200
        activities = res.json()
        assert isinstance(activities, list)
        assert len(activities) >= 1
        # Confirm events have proper relay-style fields
        assert "event_type" in activities[0]
        assert "status" in activities[0]
        assert "created_at" in activities[0]
