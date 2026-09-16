"""
GÖK SYSTEMS TECH — Projects API Endpoints
Manages isolated project workspaces, file explorer, and ZIP bundle exporting.
"""

import io
import os
import zipfile
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from gokai.apps.backend.app.core.database import get_db
from gokai.apps.backend.app.core.config import settings
from gokai.apps.backend.app.models.entities import Project
from gokai.apps.backend.app.schemas.dtos import ProjectCreate, ProjectResponse
from gokai.packages.tools.jailed_fs import JailedFileSystem

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(
        name=payload.name,
        description=payload.description,
        default_stack=payload.default_stack,
        root_path=str(settings.PROJECTS_DIR / payload.name.lower().replace(" ", "_"))
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Initialize workspace folder
    Path(project.root_path).mkdir(parents=True, exist_ok=True)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return None


@router.get("/{project_id}/files")
def list_project_files(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    fs = JailedFileSystem(Path(project.root_path))
    return fs.list_files()


@router.get("/{project_id}/files/content")
def get_file_content(project_id: str, path: str = Query(..., description="Relative file path"), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    fs = JailedFileSystem(Path(project.root_path))
    try:
        content = fs.read_file(path)
        return {"path": path, "content": content}
    except Exception as ex:
        raise HTTPException(status_code=404, detail=str(ex))


@router.get("/{project_id}/export")
def export_project_zip(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    p_dir = Path(project.root_path)
    if not p_dir.exists():
        raise HTTPException(status_code=400, detail="Workspace directory does not exist.")

    # Create in-memory zip archive
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(p_dir):
            for file in files:
                # Omit secret files
                if file.startswith(".env") and not file.endswith(".example"):
                    continue
                file_path = Path(root) / file
                rel_path = file_path.relative_to(p_dir).as_posix()
                zf.write(file_path, arcname=rel_path)

    zip_buffer.seek(0)
    filename = f"{project.name.lower().replace(' ', '_')}_export.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
