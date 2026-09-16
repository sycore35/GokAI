"""
Autonomous End-to-End Orchestrator Pipeline Test.
Simulates: User Prompt -> Plan -> Developer -> Files Created -> Tests Executed -> Review -> Success.
"""

import asyncio
import tempfile
from pathlib import Path
from gokai.packages.model_router.router import ModelRouter
from gokai.packages.orchestrator.orchestrator import OrchestratorEngine
from gokai.packages.shared.models import TaskStatus


def test_full_autonomous_orchestrator_execution():
    async def _run():
        with tempfile.TemporaryDirectory() as tmp:
            workspace_base = Path(tmp) / "projects"
            skills_dir = Path(tmp) / "skills"
            workspace_base.mkdir(parents=True, exist_ok=True)
            skills_dir.mkdir(parents=True, exist_ok=True)

            events_emitted = []

            def on_event(event_type: str, data: dict):
                events_emitted.append((event_type, data))

            model_router = ModelRouter(allow_mock_fallback=True)
            orchestrator = OrchestratorEngine(
                model_router=model_router,
                workspace_base_dir=workspace_base,
                skills_dir=skills_dir,
                max_debug_cycles=3,
                event_callback=on_event
            )

            result = await orchestrator.execute_task(
                task_id="task_e2e_calc",
                project_id="proj_e2e_calc",
                user_prompt="Create a Python calculator CLI application with unit tests",
                skip_research=True
            )

            assert result["success"] is True
            assert result["status"] == TaskStatus.COMPLETED
            assert len(result["artifacts"]) >= 2
            assert len(events_emitted) >= 3

            # Verify files on disk in workspace
            project_dir = workspace_base / "proj_e2e_calc"
            assert (project_dir / "calculator.py").exists()
            assert (project_dir / "test_calculator.py").exists()
            assert (project_dir / "SECURITY_AUDIT.md").exists()
            assert (project_dir / "PROJECT_REVIEW.md").exists()

    asyncio.run(_run())
