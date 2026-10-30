import time
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models import Document, Message, Citation, VerificationClaim
from app.services.hybrid_retriever import hybrid_retriever
from app.services.llm_provider import llm_provider
from app.services.verification_service import verification_service
from app.services.activity_service import activity_service


class RAGEngine:
    async def process_question(
        self,
        db: AsyncSession,
        query: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        document_id: Optional[str] = None,
        collection_id: Optional[str] = None,
        enable_verification: bool = True
    ) -> Dict[str, Any]:
        """
        Orchestrates full RAG workflow:
        1. Hybrid retrieval (Dense + Sparse BM25 + RRF)
        2. Context enrichment with document names and page metadata
        3. LLM generation with strict evidence grounding
        4. Citation mapping
        5. Claim-level evidence verification
        6. Activity logging
        """
        total_start = time.time()

        # 1. Hybrid Retrieval
        retrieval_res = hybrid_retriever.retrieve(
            query=query,
            top_k=settings.TOP_K_RETRIEVAL,
            document_id=document_id
        )
        raw_evidence = retrieval_res["results"]
        retrieval_latency = retrieval_res["latency_ms"]

        # Fetch document metadata for evidence chunks
        doc_ids = list({c["document_id"] for c in raw_evidence if c.get("document_id")})
        doc_map = {}
        if doc_ids:
            docs_query = await db.execute(select(Document).where(Document.id.in_(doc_ids)))
            for d in docs_query.scalars():
                doc_map[d.id] = d.filename

        # Enrich evidence chunks with document names
        enriched_evidence = []
        for c in raw_evidence:
            item = dict(c)
            item["document_name"] = doc_map.get(c.get("document_id"), "Document")
            enriched_evidence.append(item)

        # 2. LLM Generation
        answer_start = time.time()
        generation_res = await llm_provider.generate_grounded_answer(
            query=query,
            evidence_chunks=enriched_evidence,
            confidence_threshold=settings.EVIDENCE_CONFIDENCE_THRESHOLD
        )
        answer_latency = round((time.time() - answer_start) * 1000, 2)
        answer_text = generation_res["answer"]
        is_unanswerable = generation_res["is_unanswerable"]

        # 3. Citation Mapping
        citations_data = []
        if not is_unanswerable:
            for chunk in enriched_evidence[:4]:
                # Only cite if relevance is reasonable
                if chunk.get("confidence_score", 0.0) >= 0.20:
                    citations_data.append({
                        "document_id": chunk.get("document_id"),
                        "document_name": chunk.get("document_name"),
                        "page_number": chunk.get("page_number", 1),
                        "chunk_id": chunk.get("id"),
                        "snippet": chunk.get("content", "")[:280],
                        "confidence_score": chunk.get("confidence_score", 1.0)
                    })

        # 4. Evidence Verification
        verification_claims = []
        if enable_verification and not is_unanswerable:
            verification_claims = await verification_service.verify_answer_claims(
                answer=answer_text,
                evidence_passages=enriched_evidence,
                claims=generation_res.get("extracted_claims")
            )

        total_latency = round((time.time() - total_start) * 1000, 2)

        # 5. Log Activity
        await activity_service.log_event(
            db=db,
            event_type="USER_QUERY",
            status="SUCCESS" if not is_unanswerable else "WARNING",
            user_id=user_id,
            duration_ms=total_latency,
            details={
                "query": query,
                "is_unanswerable": is_unanswerable,
                "retrieval_latency_ms": retrieval_latency,
                "answer_latency_ms": answer_latency,
                "evidence_count": len(enriched_evidence),
                "citations_count": len(citations_data),
                "claims_verified": len(verification_claims),
                "provider": generation_res.get("provider")
            }
        )

        return {
            "answer": answer_text,
            "is_unanswerable": is_unanswerable,
            "provider": generation_res.get("provider"),
            "retrieval_latency_ms": retrieval_latency,
            "answer_latency_ms": answer_latency,
            "total_latency_ms": total_latency,
            "citations": citations_data,
            "verification_claims": verification_claims,
            "retrieved_evidence": enriched_evidence
        }


rag_engine = RAGEngine()
