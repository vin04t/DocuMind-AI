from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models import ActivityLog
from app.schemas import ActivityResponse

router = APIRouter(prefix="/activity", tags=["Activity Monitor"])


@router.get("", response_model=List[ActivityResponse])
@router.get("/", response_model=List[ActivityResponse], include_in_schema=False)
async def list_activities(
    event_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ActivityLog).order_by(desc(ActivityLog.created_at)).limit(limit)
    if event_type and event_type != "ALL":
        stmt = stmt.where(ActivityLog.event_type == event_type)
    if status_filter and status_filter != "ALL":
        stmt = stmt.where(ActivityLog.status == status_filter)

    res = await db.execute(stmt)
    logs = res.scalars().all()
    return [ActivityResponse.model_validate(log) for log in logs]
