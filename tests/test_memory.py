"""
Tests for MemoryManager.
"""

import gc
import tempfile
from pathlib import Path
from gokai.packages.memory.memory_manager import MemoryManager


def test_memory_manager_tiers():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "test_memory.db"
        mem = MemoryManager(db_file)

        # Level 1 Facts
        mem.add_fact("p1", "framework", "FastAPI")
        mem.add_fact("p1", "database", "SQLite")

        # Level 2 Decisions
        mem.add_decision("p1", "Chose JWT over session cookies")

        # Level 3 Milestones
        mem.add_milestone("p1", "Initial project scaffold complete")

        # Level 4 Tasks
        mem.add_task_summary("p1", "Generated auth endpoints (PASS)")

        prompt = mem.build_context_prompt("p1")

        assert "FastAPI" in prompt
        assert "SQLite" in prompt
        assert "Chose JWT" in prompt
        assert "scaffold complete" in prompt
        assert "auth endpoints" in prompt

        # Explicitly release any references
        del mem
        gc.collect()
