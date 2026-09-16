"""
GÖK SYSTEMS TECH — Activity & Audit API Endpoints
Streams and logs platform events, multi-agent operations, and operational traces.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from gokai.apps.backend.app.core.database import get_db
from gokai.apps.backend.app.models.entities import ActivityLog
from gokai.apps.backend.app.schemas.dtos import ActivityLogResponse

router = APIRouter(prefix="/activity", tags=["Activity"])


@router.get("", response_model=List[ActivityLogResponse])
def list_activity_logs(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(ActivityLog)
    if project_id:
        query = query.filter(ActivityLog.project_id == project_id)
    if task_id:
        query = query.filter(ActivityLog.task_id == task_id)

    return query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()
