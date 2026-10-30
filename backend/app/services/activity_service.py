import json
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import ActivityLog


class ActivityService:
    async def log_event(
        self,
        db: AsyncSession,
        event_type: str,
        status: str = "SUCCESS",
        user_id: Optional[str] = None,
        document_id: Optional[str] = None,
        document_name: Optional[str] = None,
        message_id: Optional[str] = None,
        duration_ms: float = 0.0,
        details: Optional[Dict[str, Any]] = None
    ) -> ActivityLog:
        """
        Records an operational event in the activity stream.
        """
        details_str = json.dumps(details) if details else None
        log_entry = ActivityLog(
            user_id=user_id,
            event_type=event_type,
            status=status,
            document_id=document_id,
            document_name=document_name,
            message_id=message_id,
            duration_ms=round(duration_ms, 2),
            details_json=details_str
        )
        db.add(log_entry)
        await db.flush()
        return log_entry


activity_service = ActivityService()
