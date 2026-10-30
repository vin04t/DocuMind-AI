from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models import VerificationClaim, Document
from app.schemas import VerificationClaimResponse
from app.services.verification_service import verification_service
from app.services.hybrid_retriever import hybrid_retriever

router = APIRouter(prefix="/verification", tags=["Evidence Verification"])


@router.get("/claims", response_model=List[VerificationClaimResponse])
async def list_verified_claims(
    status_filter: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(VerificationClaim).order_by(desc(VerificationClaim.created_at)).limit(limit)
    if status_filter and status_filter != "ALL":
        stmt = stmt.where(VerificationClaim.status == status_filter)

    res = await db.execute(stmt)
    claims = res.scalars().all()
    return [VerificationClaimResponse.model_validate(c) for c in claims]


from pydantic import BaseModel

class CustomClaimRequest(BaseModel):
    claim_text: Optional[str] = None
    claim: Optional[str] = None
    document_id: Optional[str] = None


@router.post("/verify")
@router.post("/verify-claim", include_in_schema=False)
async def verify_custom_claim(
    payload: CustomClaimRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Performs ad-hoc verification of a user-submitted claim against indexed documents.
    """
    target_claim = payload.claim_text or payload.claim
    if not target_claim or len(target_claim.strip()) < 5:
        raise HTTPException(status_code=400, detail="Claim text must be provided.")

    # Retrieve relevant evidence passages
    retrieval_res = hybrid_retriever.retrieve(query=target_claim, top_k=5, document_id=payload.document_id)
    raw_evidence = retrieval_res["results"]

    # Enrich with document names
    doc_ids = list({c["document_id"] for c in raw_evidence if c.get("document_id")})
    doc_map = {}
    if doc_ids:
        docs_query = await db.execute(select(Document).where(Document.id.in_(doc_ids)))
        for d in docs_query.scalars():
            doc_map[d.id] = d.filename

    enriched_evidence = []
    for c in raw_evidence:
        item = dict(c)
        item["document_name"] = doc_map.get(c.get("document_id"), "Document")
        enriched_evidence.append(item)

    verified = await verification_service.verify_answer_claims(
        answer=target_claim,
        evidence_passages=enriched_evidence,
        claims=[target_claim]
    )

    if verified:
        return verified[0]
    return {
        "claim_text": target_claim,
        "status": "NOT_SUPPORTED",
        "rationale": "No relevant textual evidence found in the document corpus."
    }
