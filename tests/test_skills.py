"""
Tests for SkillManager.
"""

from pathlib import Path
from gokai.packages.skills.skill_manager import SkillManager


def test_skill_manager_matching():
    skills_dir = Path(__file__).resolve().parent.parent / "skills"
    manager = SkillManager(skills_dir)

    # Should match python skill
    matches = manager.match_skills("Create a Python CLI calculator tool")
    assert len(matches) >= 1
    assert any(m.name == "python-engineering" for m in matches)

    # Should match fastapi skill
    matches_fastapi = manager.match_skills("Build a FastAPI REST backend with endpoints")
    assert len(matches_fastapi) >= 1
    assert any(m.name == "fastapi-services" for m in matches_fastapi)
