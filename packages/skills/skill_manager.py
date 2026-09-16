"""
GÖK SYSTEMS TECH — Skills Subsystem
Discovers, validates, manages, and matches modular domain skills to user tasks.
Supports built-in and custom user-created skills.
"""

import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from gokai.packages.shared.logger import get_logger

logger = get_logger("skill_manager")


class SkillMetadata(BaseModel):
    name: str
    description: str
    when_to_use: str = ""
    tags: List[str] = Field(default_factory=list)
    instructions: str = ""
    path: str = ""
    is_builtin: bool = True
    enabled: bool = True


class SkillManager:
    """Manages skill discovery, parsing, validation, and context matching."""

    def __init__(self, skills_root: Path, custom_skills_root: Optional[Path] = None):
        self.skills_root = Path(skills_root)
        self.custom_skills_root = Path(custom_skills_root) if custom_skills_root else (self.skills_root.parent / "data" / "custom_skills")
        self.custom_skills_root.mkdir(parents=True, exist_ok=True)
        self.disabled_file = self.custom_skills_root / "_disabled_skills.json"

        self.skills: Dict[str, SkillMetadata] = {}
        self.reload_skills()

    def _get_disabled_names(self) -> set:
        if self.disabled_file.exists():
            try:
                return set(json.loads(self.disabled_file.read_text(encoding="utf-8")))
            except Exception:
                pass
        return set()

    def _save_disabled_names(self, disabled_set: set):
        self.disabled_file.write_text(json.dumps(list(disabled_set)), encoding="utf-8")

    def reload_skills(self):
        """Scans both built-in and custom skills directories for SKILL.md files."""
        self.skills.clear()
        disabled = self._get_disabled_names()

        # 1. Load built-in skills
        if self.skills_root.exists():
            for skill_dir in self.skills_root.iterdir():
                if skill_dir.is_dir():
                    skill_file = skill_dir / "SKILL.md"
                    if skill_file.exists():
                        try:
                            meta = self._parse_skill_file(skill_file, is_builtin=True)
                            meta.enabled = (meta.name not in disabled)
                            self.skills[meta.name] = meta
                        except Exception as ex:
                            logger.warning(f"Failed to parse skill at {skill_file}: {ex}")

        # 2. Load custom user skills
        if self.custom_skills_root.exists():
            for skill_dir in self.custom_skills_root.iterdir():
                if skill_dir.is_dir() and not skill_dir.name.startswith("_"):
                    skill_file = skill_dir / "SKILL.md"
                    if skill_file.exists():
                        try:
                            meta = self._parse_skill_file(skill_file, is_builtin=False)
                            meta.enabled = (meta.name not in disabled)
                            self.skills[meta.name] = meta
                        except Exception as ex:
                            logger.warning(f"Failed to parse custom skill at {skill_file}: {ex}")

        logger.info(f"Loaded {len(self.skills)} domain skills ({sum(1 for s in self.skills.values() if s.enabled)} enabled)")

    def _parse_skill_file(self, skill_file: Path, is_builtin: bool = True) -> SkillMetadata:
        content = skill_file.read_text(encoding="utf-8")
        meta = self.validate_skill_content(content, fallback_name=skill_file.parent.name)
        meta.path = str(skill_file)
        meta.is_builtin = is_builtin
        return meta

    @staticmethod
    def validate_skill_content(content: str, fallback_name: str = "custom-skill") -> SkillMetadata:
        """Validates and parses SKILL.md markdown text with YAML frontmatter."""
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        if not match:
            return SkillMetadata(
                name=fallback_name,
                description="Custom domain engineering skill",
                instructions=content.strip(),
                tags=["custom"],
                is_builtin=False
            )

        fm_text, instructions = match.groups()
        name = fallback_name
        desc = ""
        when_to_use = ""
        tags = []

        for line in fm_text.splitlines():
            line = line.strip()
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip().strip('"\'')
            elif line.startswith("description:"):
                desc = line.split(":", 1)[1].strip().strip('"\'')
            elif line.startswith("when_to_use:"):
                when_to_use = line.split(":", 1)[1].strip().strip('"\'')
            elif line.startswith("tags:"):
                raw_tags = line.split(":", 1)[1].strip().strip("[]")
                tags = [t.strip().strip('"\'') for t in raw_tags.split(",") if t.strip()]

        clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "", name.lower().replace(" ", "-")) or fallback_name

        return SkillMetadata(
            name=clean_name,
            description=desc or "Custom skill description",
            when_to_use=when_to_use,
            tags=tags,
            instructions=instructions.strip(),
            is_builtin=False
        )

    def create_custom_skill(
        self,
        name: str,
        description: str,
        when_to_use: str = "",
        tags: Optional[List[str]] = None,
        instructions: str = ""
    ) -> SkillMetadata:
        """Creates and writes a new custom domain skill."""
        clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "", name.lower().replace(" ", "-"))
        if not clean_name:
            raise ValueError("Invalid skill name")

        skill_dir = self.custom_skills_root / clean_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"

        tag_list = tags or ["custom"]
        frontmatter = (
            f"---\n"
            f'name: "{clean_name}"\n'
            f'description: "{description}"\n'
            f'when_to_use: "{when_to_use}"\n'
            f'tags: {json.dumps(tag_list)}\n'
            f"---\n\n"
        )
        body = instructions.strip() or f"# {clean_name}\n\nGuidelines for {clean_name}."
        skill_file.write_text(frontmatter + body, encoding="utf-8")

        # Ensure newly created skill starts enabled
        disabled = self._get_disabled_names()
        if clean_name in disabled:
            disabled.remove(clean_name)
            self._save_disabled_names(disabled)

        self.reload_skills()
        return self.skills[clean_name]

    def update_custom_skill(
        self,
        name: str,
        description: Optional[str] = None,
        when_to_use: Optional[str] = None,
        tags: Optional[List[str]] = None,
        instructions: Optional[str] = None
    ) -> SkillMetadata:
        """Updates an existing custom skill."""
        if name not in self.skills:
            raise KeyError(f"Skill '{name}' not found")

        current = self.skills[name]
        if current.is_builtin:
            raise ValueError("Cannot edit built-in core skills directly")

        new_desc = description if description is not None else current.description
        new_when = when_to_use if when_to_use is not None else current.when_to_use
        new_tags = tags if tags is not None else current.tags
        new_inst = instructions if instructions is not None else current.instructions

        return self.create_custom_skill(
            name=name,
            description=new_desc,
            when_to_use=new_when,
            tags=new_tags,
            instructions=new_inst
        )

    def delete_custom_skill(self, name: str) -> bool:
        """Deletes a custom skill directory."""
        if name not in self.skills:
            return False
        skill = self.skills[name]
        if skill.is_builtin:
            raise ValueError("Built-in core skills cannot be deleted")

        skill_dir = Path(skill.path).parent
        if skill_dir.exists() and self.custom_skills_root in skill_dir.parents:
            shutil.rmtree(skill_dir)
            disabled = self._get_disabled_names()
            if name in disabled:
                disabled.remove(name)
                self._save_disabled_names(disabled)
            self.reload_skills()
            return True
        return False

    def toggle_skill(self, name: str, enabled: Optional[bool] = None) -> bool:
        """Enables or disables a skill."""
        if name not in self.skills:
            raise KeyError(f"Skill '{name}' not found")

        skill = self.skills[name]
        new_status = not skill.enabled if enabled is None else enabled
        skill.enabled = new_status

        disabled = self._get_disabled_names()
        if new_status:
            disabled.discard(name)
        else:
            disabled.add(name)
        self._save_disabled_names(disabled)

        return new_status

    def match_skills(self, task_prompt: str, max_skills: int = 3) -> List[SkillMetadata]:
        """Matches task against registered enabled skills using keyword and tag scoring."""
        prompt_lower = task_prompt.lower()
        scored: List[Tuple[int, SkillMetadata]] = []

        for skill in self.skills.values():
            if not skill.enabled:
                continue

            score = 0
            if skill.name.lower() in prompt_lower:
                score += 5
            for tag in skill.tags:
                if tag.lower() in prompt_lower:
                    score += 3
            if skill.when_to_use and any(w in prompt_lower for w in skill.when_to_use.lower().split() if len(w) > 3):
                score += 2

            if score > 0:
                scored.append((score, skill))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:max_skills]]
