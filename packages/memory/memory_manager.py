"""
GÖK SYSTEMS TECH — Hierarchical Memory Subsystem
Persists project facts, architectural decisions, milestones, and task outcomes.
Optimizes context window by keeping memory token overhead below 1,500 tokens.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from gokai.packages.shared.logger import get_logger

logger = get_logger("memory_manager")


class MemoryManager:
    """Manages 4-tier persistent hierarchical memory per project."""

    def __init__(self, db_path: Path | str):
        if str(db_path) == ":memory:":
            self.db_path = ":memory:"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    tier INTEGER NOT NULL, -- 1: Facts, 2: Decisions, 3: Evolution, 4: Tasks
                    key TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_proj ON memory_entries(project_id, tier);")
            conn.commit()
        finally:
            conn.close()

    def add_fact(self, project_id: str, key: str, value: str):
        """Level 1: Static project truths (framework, database, ports)."""
        self._upsert_entry(project_id, 1, key, value)

    def add_decision(self, project_id: str, decision: str):
        """Level 2: Architectural and technical decisions."""
        self._insert_entry(project_id, 2, "decision", decision)

    def add_milestone(self, project_id: str, milestone: str):
        """Level 3: Important evolution events."""
        self._insert_entry(project_id, 3, "milestone", milestone)

    def add_task_summary(self, project_id: str, task_summary: str):
        """Level 4: Recent completed task summaries."""
        self._insert_entry(project_id, 4, "task_summary", task_summary)

    def _upsert_entry(self, project_id: str, tier: int, key: str, content: str):
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM memory_entries WHERE project_id = ? AND tier = ? AND key = ?
            """, (project_id, tier, key))
            cursor.execute("""
                INSERT INTO memory_entries (project_id, tier, key, content)
                VALUES (?, ?, ?, ?)
            """, (project_id, tier, key, content))
            conn.commit()
        finally:
            conn.close()

    def _insert_entry(self, project_id: str, tier: int, key: str, content: str):
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memory_entries (project_id, tier, key, content)
                VALUES (?, ?, ?, ?)
            """, (project_id, tier, key, content))
            conn.commit()
        finally:
            conn.close()

    def get_entries(self, project_id: str, tier: Optional[int] = None) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            if tier:
                cursor.execute("""
                    SELECT id, tier, key, content, created_at FROM memory_entries
                    WHERE project_id = ? AND tier = ? ORDER BY id DESC LIMIT 20
                """, (project_id, tier))
            else:
                cursor.execute("""
                    SELECT id, tier, key, content, created_at FROM memory_entries
                    WHERE project_id = ? ORDER BY tier ASC, id DESC LIMIT 50
                """, (project_id,))
            rows = cursor.fetchall()
            return [{"id": r[0], "tier": r[1], "key": r[2], "content": r[3], "created_at": r[4]} for r in rows]
        finally:
            conn.close()

    def build_context_prompt(self, project_id: str) -> str:
        """Builds a token-optimized markdown summary of project memory."""
        entries = self.get_entries(project_id)
        if not entries:
            return ""

        facts = [f"- {e['key']}: {e['content']}" for e in entries if e["tier"] == 1]
        decisions = [f"- {e['content']}" for e in entries if e["tier"] == 2]
        milestones = [f"- {e['content']}" for e in entries if e["tier"] == 3][:5]
        tasks = [f"- {e['content']}" for e in entries if e["tier"] == 4][:3]

        sections = []
        if facts:
            sections.append("### Project Facts\n" + "\n".join(facts))
        if decisions:
            sections.append("### Architectural Decisions\n" + "\n".join(decisions))
        if milestones:
            sections.append("### Recent Milestones\n" + "\n".join(milestones))
        if tasks:
            sections.append("### Recent Tasks\n" + "\n".join(tasks))

        return "\n\n".join(sections)
