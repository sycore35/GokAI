# GÖKAI Hierarchical Memory Specification

> **GÖK SYSTEMS TECH** — Cross-Session Cognitive Core  
> **Status:** Standardized Architecture Specification  

---

## 1. Objectives & Anti-Pattern Avoidance

A critical flaw in naive AI coding systems is **blind context stuffing**—dumping the entire history of conversations, raw code files, and build logs into the model prompt on every turn. This leads to:
1. Catastrophic token consumption and ballooning API costs.
2. Context window saturation and degradation of model attention (the *“Lost in the Middle”* effect).
3. Repetitive loops and hallucinations.

GökAI implements **Hierarchical Memory Isolation**, condensing and tiering project knowledge into 4 distinct abstraction levels stored persistently per project.

---

## 2. The 4-Tier Memory Hierarchy

```text
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 1: PROJECT FACTS (Static Truths)                      │
│ - Tech Stack: FastAPI + React + SQLite                      │
│ - Port Bindings: Backend :8000, Frontend :3000              │
│ - Authentication: JWT (HS256)                               │
│ - Strict Design Tokens: Dark cyberpunk (#0B0F19, #00FFCC)   │
├─────────────────────────────────────────────────────────────┤
│ LEVEL 2: ARCHITECTURAL DECISIONS (ADRs)                     │
│ - "User explicitly rejected Docker in favor of local venv"  │
│ - "Adopted SQLAlchemy 2.0 Async Session pattern"            │
│ - "Chose Tailwind v4 CSS-first token configuration"         │
├─────────────────────────────────────────────────────────────┤
│ LEVEL 3: SIGNIFICANT EVOLUTION (Milestones & Diffs)         │
│ - [2026-09-13]: Migrated database schema to add portfolios  │
│ - [2026-09-13]: Integrated Playwright browser test suite    │
├─────────────────────────────────────────────────────────────┤
│ LEVEL 4: TASK HISTORY (Rolling Window Summaries)            │
│ - Task #1: Setup initial repository structure (PASS)        │
│ - Task #2: Generate auth endpoints and unit tests (PASS)    │
│ - Task #3: Fix CORS header regression in middleware (FIXED) │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Storage Model & Schemas

Memory entries are stored per-project in relational database tables (`memory_entries`) backed by SQLite/PostgreSQL:

```python
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class MemoryTier(str, Enum):
    LEVEL_1_FACTS = "facts"
    LEVEL_2_DECISIONS = "decisions"
    LEVEL_3_EVOLUTION = "evolution"
    LEVEL_4_TASKS = "tasks"

class MemoryEntry(BaseModel):
    id: str
    project_id: str
    tier: MemoryTier
    key: str
    content: str
    confidence: float = 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 4. Context Builder & Token Optimization

When an agent is invoked, the `ContextBuilder` dynamically constructs a token-efficient prompt payload:

```text
Prompt Budget: 8,000 tokens allocated for Context
  ├── Level 1 Facts: Always included (compact key-value bullet points: ~200 tokens)
  ├── Level 2 Decisions: Always included (~300 tokens)
  ├── Level 3 Milestones: Summarized top 5 most recent (~400 tokens)
  ├── Level 4 Tasks: Last 3 completed task outcomes (~500 tokens)
  └── Relevant Code Chunks: Injected via AST / Symbol Code Search (~4,000 tokens)
```

Total baseline memory overhead is consistently kept **under 1,500 tokens**, leaving the vast majority of the model's context window for actual code reasoning and syntax generation.
