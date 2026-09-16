"""
Unit tests for specialist agents: Developer, Tester, Debugger, Security, Reviewer.
"""

import asyncio
import tempfile
from pathlib import Path
from gokai.packages.model_router.router import ModelRouter
from gokai.packages.tools.tool_registry import ToolRegistry
from gokai.packages.shared.models import TaskContext, ArtifactType
from gokai.packages.agents.developer import DeveloperAgent
from gokai.packages.agents.tester import TesterAgent
from gokai.packages.agents.security import SecurityAgent
from gokai.packages.agents.reviewer import ReviewerAgent


def test_agent_workflows():
    async def _run():
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            registry = ToolRegistry(workspace)
            router = ModelRouter(allow_mock_fallback=True)

            context = TaskContext(
                task_id="task_test_01",
                project_id="proj_test_01",
                user_prompt="Create a Python calculator",
                workspace_path=str(workspace)
            )

            # 1. Developer Agent generates files
            dev = DeveloperAgent(router, registry)
            dev_result = await dev.execute(context)
            assert dev_result.success is True
            assert registry.fs.file_exists("calculator.py")

            # 2. Security Agent scans files
            sec = SecurityAgent(router, registry)
            sec_result = await sec.execute(context)
            assert sec_result.success is True
            assert registry.fs.file_exists("SECURITY_AUDIT.md")

            # 3. Tester Agent runs tests
            tester = TesterAgent(router, registry)
            test_result = await tester.execute(context)
            assert registry.fs.file_exists("test_run_report.txt")

            # 4. Reviewer Agent audits deliverables
            rev = ReviewerAgent(router, registry)
            rev_result = await rev.execute(context)
            assert rev_result.success is True
            assert registry.fs.file_exists("PROJECT_REVIEW.md")

    asyncio.run(_run())
