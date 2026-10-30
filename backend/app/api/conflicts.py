from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models import ConflictRecord, Document, DocumentChunk
from app.schemas import ConflictResponse, ConflictStatusUpdateRequest
from app.services.conflict_detector import conflict_detector
from app.services.activity_service import activity_service
from app.api.auth import get_current_user

router = APIRouter(prefix="/conflicts", tags=["Conflict Detection"])


@router.get("", response_model=List[ConflictResponse])
@router.get("/", response_model=List[ConflictResponse], include_in_schema=False)
async def list_conflicts(
    status_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ConflictRecord).order_by(desc(ConflictRecord.created_at))
    if status_filter and status_filter != "ALL":
        stmt = stmt.where(ConflictRecord.review_status == status_filter)

    res = await db.execute(stmt)
    conflicts = res.scalars().all()
    return [ConflictResponse.model_validate(c) for c in conflicts]


@router.post("/detect", response_model=List[ConflictResponse])
async def run_conflict_detection(
    db: AsyncSession = Depends(get_db)
):
    """
    Scans all indexed documents and runs cross-document discrepancy detection.
    """
    # Fetch all indexed documents
    docs_res = await db.execute(select(Document).where(Document.status == "INDEXED"))
    docs = docs_res.scalars().all()

    if len(docs) < 2:
        return []

    # Gather chunks for each document
    documents_with_chunks = []
    for doc in docs:
        chunks_res = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == doc.id)
            .order_by(DocumentChunk.chunk_index)
        )
        chunks = chunks_res.scalars().all()
        documents_with_chunks.append({
            "id": doc.id,
            "filename": doc.filename,
            "chunks": [
                {
                    "content": c.content,
                    "page_number": c.page_number
                }
                for c in chunks
            ]
        })

    detected_conflicts = conflict_detector.detect_conflicts_across_documents(documents_with_chunks)

    saved_records = []
    for c in detected_conflicts:
        # Check if identical conflict already exists
        existing = await db.execute(
            select(ConflictRecord).where(
                ConflictRecord.document_a_id == c["document_a_id"],
                ConflictRecord.document_b_id == c["document_b_id"],
                ConflictRecord.conflict_type == c["conflict_type"]
            )
        )
        if existing.scalars().first():
            continue

        record = ConflictRecord(
            document_a_id=c["document_a_id"],
            document_a_name=c["document_a_name"],
            page_a=c["page_a"],
            statement_a=c["statement_a"],
            passage_a=c["passage_a"],
            document_b_id=c["document_b_id"],
            document_b_name=c["document_b_name"],
            page_b=c["page_b"],
            statement_b=c["statement_b"],
            passage_b=c["passage_b"],
            conflict_type=c["conflict_type"],
            explanation=c["explanation"],
            review_status="NEEDS_INVESTIGATION"
        )
        db.add(record)
        saved_records.append(record)

    await db.commit()

    # Log conflict detection activity
    await activity_service.log_event(
        db, "CONFLICT_DETECTION", "SUCCESS",
        details={
            "documents_scanned": len(docs),
            "new_conflicts_found": len(saved_records)
        }
    )

    # Return all current conflicts
    all_res = await db.execute(select(ConflictRecord).order_by(desc(ConflictRecord.created_at)))
    return [ConflictResponse.model_validate(cr) for cr in all_res.scalars().all()]


@router.patch("/{conflict_id}/status", response_model=ConflictResponse)
async def update_conflict_status(
    conflict_id: str,
    update_in: ConflictStatusUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(ConflictRecord).where(ConflictRecord.id == conflict_id))
    record = res.scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="Conflict record not found.")

    record.review_status = update_in.review_status
    if update_in.resolution_notes is not None:
        record.resolution_notes = update_in.resolution_notes

    await db.commit()
    await db.refresh(record)
    return ConflictResponse.model_validate(record)
