# GÖKAI Skills Subsystem Specification

> **GÖK SYSTEMS TECH** — Extensible Domain Knowledge Engine  
> **Status:** Standardized Architecture Specification  

---

## 1. Overview

The **Skills Subsystem** enables GökAI to ingest, validate, and activate modular domain expertise on-demand. Instead of forcing monolithic prompts into every agent execution, skills act as discrete, plug-and-play capability packages.

Users and developers can create or import custom skills (e.g., `fastapi`, `react-nextjs`, `electronics-plc`, `sql-optimization`, `security-auditing`) to enrich agent performance without altering the core codebase.

---

## 2. Skill Directory Structure

Every skill lives in its own directory conforming to the standard layout:

```text
skills/
└── {skill_name}/
    ├── SKILL.md            # Mandatory: Metadata, trigger conditions & instructions
    ├── templates/          # Optional: Reusable boilerplate code files
    ├── references/         # Optional: API cheat-sheets and architectural rules
    ├── examples/           # Optional: Few-shot input/output demonstrations
    └── tools/              # Optional: Custom Python scripts/tools (Sandboxed)
```

---

## 3. `SKILL.md` Specification

The `SKILL.md` file uses YAML frontmatter parsed by strict Pydantic models:

```markdown
---
name: fastapi-jwt-auth
version: 1.0.0
description: Production-grade FastAPI authentication using JWT and passlib bcrypt
when_to_use: "Use when creating user signup, login, OAuth2, or protected endpoints in FastAPI"
tags: ["fastapi", "python", "auth", "security", "jwt"]
required_packages: ["fastapi", "python-jose[cryptography]", "passlib[bcrypt]"]
risk_level: "low"
---

# FastAPI JWT Authentication Guide

## Architecture Pattern
1. Use OAuth2PasswordBearer with tokenUrl="api/auth/token".
2. Store passwords hashed with bcrypt; never store plaintext passwords.
3. Validate tokens in a dependency `get_current_user`.

## Implementation Rules
- Always specify expiration time (`exp` claim) on JWT tokens (default: 30 minutes).
- Return standard HTTP 401 Unauthorized with `WWW-Authenticate: Bearer` header on failure.
```

---

## 4. Dynamic Skill Matcher & Discovery

GökAI does **not** load all skills simultaneously. To conserve context window and prevent conflicting instructions:

1. **Analysis Phase**: When the user provides a prompt, the `SkillMatcher` extracts intent keywords and technology tags.
2. **Scoring Phase**: Matches against skill `when_to_use` semantics and tag sets.
3. **Activation Phase**: Only the top matching skills (maximum 3 per task) are loaded into the executing agent's working context.

```python
class SkillMatcher:
    def match_skills(
        self,
        task_prompt: str,
        available_skills: List[SkillMetadata],
        max_skills: int = 3
    ) -> List[SkillMetadata]:
        """Matches task against skill registry using semantic tagging and keyword triggers."""
        # Returns ordered list of relevant skills
        pass
```

---

## 5. Untrusted Skill Ingestion & Safety Verification

When a user imports a third-party skill from a ZIP archive or Git repository, GökAI executes an automated security audit before registering it:

1. **Static AST & Content Inspection**: Scans `SKILL.md` and any included scripts for malicious prompt injections, hidden instructions, or destructive shell commands.
2. **Permission Declaration**: Custom tools within `tools/` must explicitly state their required permissions (`network`, `filesystem.write`).
3. **Quarantine Sandbox**: Custom skill scripts are executed strictly inside the isolated Sandbox container, never on the host machine.
