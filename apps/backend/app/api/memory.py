"""
GÖK SYSTEMS TECH — Memory API Endpoints
Manages persistent project memory (facts, decisions, evolution, task history).
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from gokai.apps.backend.app.core.database import get_db
from gokai.apps.backend.app.models.entities import MemoryEntry, Project
from gokai.apps.backend.app.schemas.dtos import MemoryEntryCreate, MemoryEntryResponse

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("", response_model=List[MemoryEntryResponse])
def get_memory_entries(
    project_id: str = Query(..., description="Target Project ID"),
    tier: Optional[int] = Query(None, description="Filter by tier (1: Facts, 2: Decisions, 3: Evolution, 4: Tasks)"),
    db: Session = Depends(get_db)
):
    query = db.query(MemoryEntry).filter(MemoryEntry.project_id == project_id)
    if tier is not None:
        query = query.filter(MemoryEntry.tier == tier)
    return query.order_by(MemoryEntry.created_at.desc()).all()


@router.post("", response_model=MemoryEntryResponse, status_code=201)
def add_memory_entry(payload: MemoryEntryCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    entry = MemoryEntry(
        project_id=payload.project_id,
        tier=payload.tier,
        key=payload.key,
        content=payload.content
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204)
def delete_memory_entry(entry_id: str, db: Session = Depends(get_db)):
    entry = db.query(MemoryEntry).filter(MemoryEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    db.delete(entry)
    db.commit()
    return None
