"""
GÖK SYSTEMS TECH — Skills Management API
Manages built-in and custom domain engineering skills, enabling runtime inspection,
creation, editing, deletion, toggling, and validation directly from the Web UI.
"""

from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any, Optional
from gokai.apps.backend.app.core.config import settings
from gokai.apps.backend.app.schemas.dtos import SkillCreate, SkillUpdate, SkillResponse
from gokai.packages.skills.skill_manager import SkillManager

router = APIRouter(prefix="/skills", tags=["Skills"])

# Singleton skill manager
_skill_manager = SkillManager(settings.SKILLS_DIR)


def get_skill_manager() -> SkillManager:
    return _skill_manager


@router.get("", response_model=List[SkillResponse])
def list_skills():
    """Returns all installed domain skills (built-in and custom)."""
    manager = get_skill_manager()
    manager.reload_skills()
    return [
        SkillResponse(
            name=s.name,
            description=s.description,
            when_to_use=s.when_to_use,
            tags=s.tags,
            instructions=s.instructions,
            path=s.path,
            is_builtin=s.is_builtin,
            enabled=s.enabled
        )
        for s in manager.skills.values()
    ]


@router.post("", response_model=SkillResponse)
def create_skill(payload: SkillCreate):
    """Creates a new custom domain engineering skill."""
    manager = get_skill_manager()
    try:
        created = manager.create_custom_skill(
            name=payload.name,
            description=payload.description,
            when_to_use=payload.when_to_use,
            tags=payload.tags,
            instructions=payload.instructions
        )
        return SkillResponse(
            name=created.name,
            description=created.description,
            when_to_use=created.when_to_use,
            tags=created.tags,
            instructions=created.instructions,
            path=created.path,
            is_builtin=created.is_builtin,
            enabled=created.enabled
        )
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.put("/{name}", response_model=SkillResponse)
def update_skill(name: str, payload: SkillUpdate):
    """Updates an existing custom skill."""
    manager = get_skill_manager()
    try:
        updated = manager.update_custom_skill(
            name=name,
            description=payload.description,
            when_to_use=payload.when_to_use,
            tags=payload.tags,
            instructions=payload.instructions
        )
        if payload.enabled is not None:
            manager.toggle_skill(name, payload.enabled)
            updated.enabled = payload.enabled

        return SkillResponse(
            name=updated.name,
            description=updated.description,
            when_to_use=updated.when_to_use,
            tags=updated.tags,
            instructions=updated.instructions,
            path=updated.path,
            is_builtin=updated.is_builtin,
            enabled=updated.enabled
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.delete("/{name}")
def delete_skill(name: str):
    """Deletes a custom skill."""
    manager = get_skill_manager()
    try:
        success = manager.delete_custom_skill(name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")
        return {"status": "deleted", "name": name}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/{name}/toggle")
def toggle_skill_status(name: str, enabled: Optional[bool] = None):
    """Enables or disables a domain skill."""
    manager = get_skill_manager()
    try:
        new_status = manager.toggle_skill(name, enabled)
        return {"name": name, "enabled": new_status}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")


@router.post("/validate")
def validate_skill_file(content: str = Body(..., media_type="text/plain")):
    """Validates raw SKILL.md markdown text and extracts frontmatter."""
    try:
        meta = SkillManager.validate_skill_content(content)
        return {
            "valid": True,
            "name": meta.name,
            "description": meta.description,
            "when_to_use": meta.when_to_use,
            "tags": meta.tags,
            "has_instructions": bool(meta.instructions.strip())
        }
    except Exception as ex:
        return {"valid": False, "error": str(ex)}
