"""
GÖK SYSTEMS TECH — Test Agent
Discovers, generates, and executes test suites to verify software functionality.
Supports Python (pytest, unittest fallback) and JavaScript/TypeScript (npm test, npm run build).
Outputs structured test execution results.
"""

import os
import sys
import time
from typing import Optional, List, Dict, Any
from gokai.packages.agents.base import BaseAgent, AgentPermissions
from gokai.packages.shared.models import (
    AgentMessage,
    AgentRunResult,
    TaskContext,
    Artifact,
    ArtifactType,
)
from gokai.packages.model_router.provider import ModelMessage
from gokai.packages.shared.logger import get_logger

logger = get_logger("tester_agent")


class TesterAgent(BaseAgent):
    """Specialist responsible for test generation, execution verification, and structured reporting."""

    __test__ = False
    name = "tester"
    description = "QA engineer responsible for testing, validating code execution, and verifying assertions."
    permissions = AgentPermissions(can_read_filesystem=True, can_write_filesystem=True, can_execute_terminal=True)
    allowed_tools = ["read_file", "write_file", "list_files", "execute_command"]

    def get_system_prompt(self, context: TaskContext) -> str:
        return (
            "You are the QA Test Automation Specialist for GÖK SYSTEMS TECH (GökAI).\n"
            "Your objective is to verify code through automated testing.\n"
            "Write comprehensive tests that verify core logic, edge cases, and error handling.\n"
            "Format test files strictly as:\n"
            "=== FILE: test_feature.py ===\n"
            "```python\n"
            "[complete test code]\n"
            "```\n"
        )

    async def execute(
        self,
        context: TaskContext,
        input_message: Optional[AgentMessage] = None
    ) -> AgentRunResult:
        logger.info(f"TesterAgent verifying workspace for task: {context.task_id}")
        start_time = time.perf_counter()

        files = self.tool_registry.fs.list_files()
        has_python = any(f["path"].endswith(".py") for f in files)
        has_js = any(f["path"].endswith((".js", ".ts", ".json")) for f in files)
        has_package_json = any(f["path"] == "package.json" for f in files)

        artifacts: List[Artifact] = []

        # 1. Check if tests exist. If not, generate tests for detected code files.
        test_files = [
            f for f in files
            if ("test" in f["path"].lower() or "spec" in f["path"].lower())
            and f["path"].endswith((".py", ".js", ".ts"))
        ]

        if not test_files:
            logger.info("No test files detected. Generating automated test suite...")
            code_files = [
                f for f in files
                if f["path"].endswith((".py", ".js", ".ts"))
                and not f["is_dir"]
                and "test" not in f["path"].lower()
            ]
            code_summary = ""
            for cf in code_files:
                try:
                    code_summary += f"\nFile: {cf['path']}\n```\n{self.tool_registry.fs.read_file(cf['path'])}\n```\n"
                except Exception:
                    pass

            if code_summary:
                prompt = (
                    f"Objective: {context.user_prompt}\n\n"
                    f"Source code to test:\n{code_summary}\n\n"
                    "Please generate a complete test suite covering primary functionality and edge cases."
                )

                messages = [
                    ModelMessage(role="system", content=self.get_system_prompt(context)),
                    ModelMessage(role="user", content=prompt),
                ]

                resp = await self.model_router.generate_completion(messages=messages)
                import re
                file_blocks = re.findall(
                    r"===\s*FILE:\s*([^\s=]+)\s*===\s*```[a-zA-Z0-9_-]*\n(.*?)\n```",
                    resp.content,
                    re.DOTALL,
                )
                if not file_blocks:
                    single_block = re.search(r"```(?:python|javascript|typescript)?\n(.*?)\n```", resp.content, re.DOTALL)
                    if single_block:
                        filename = "test_app.py" if has_python else "test_app.js"
                        file_blocks = [(filename, single_block.group(1).strip())]

                for t_path, t_code in file_blocks:
                    clean_path = t_path.strip().replace("\\", "/")
                    self.tool_registry.fs.write_file(clean_path, t_code.strip())
                    art = Artifact(
                        project_id=context.project_id,
                        task_id=context.task_id,
                        type=ArtifactType.CODE,
                        name=clean_path,
                        path=clean_path,
                        content=t_code.strip(),
                        created_by=self.name,
                    )
                    artifacts.append(art)

        # 2. Determine test execution commands based on project stack
        py_exe = sys.executable

        if has_python:
            # Try pytest first
            test_cmd = f'"{py_exe}" -m pytest -v'
            logger.info(f"Executing Python test command: {test_cmd}")
            exec_result = await self.tool_registry.terminal.execute_command(test_cmd, timeout_seconds=45)

            # If pytest module not available (exit code != 0 with 'No module named pytest'), fallback to unittest
            if exec_result.exit_code != 0 and "No module named pytest" in exec_result.stderr:
                logger.info("pytest not found in environment, falling back to unittest discovery...")
                test_cmd = f'"{py_exe}" -m unittest discover -v'
                exec_result = await self.tool_registry.terminal.execute_command(test_cmd, timeout_seconds=45)

        elif has_package_json:
            # JavaScript / Node project
            logger.info("Executing npm test...")
            exec_result = await self.tool_registry.terminal.execute_command("npm test", timeout_seconds=60)
            if exec_result.exit_code != 0 and "no test specified" in (exec_result.stdout + exec_result.stderr).lower():
                logger.info("No test script in package.json, verifying build with npm run build...")
                exec_result = await self.tool_registry.terminal.execute_command("npm run build", timeout_seconds=60)
        else:
            # General command verification
            main_files = [f["path"] for f in files if f["path"].endswith(".py")]
            if main_files:
                target = main_files[0]
                exec_result = await self.tool_registry.terminal.execute_command(f'"{py_exe}" "{target}"', timeout_seconds=30)
            else:
                exec_result = await self.tool_registry.terminal.execute_command(f'"{py_exe}" --version', timeout_seconds=10)

        passed = exec_result.exit_code == 0
        summary = (
            f"Tests {'PASSED' if passed else 'FAILED'} (Exit code: {exec_result.exit_code}) in {exec_result.duration_ms:.0f}ms.\n"
            f"Stdout: {exec_result.stdout[-300:] if exec_result.stdout else 'None'}\n"
            f"Stderr: {exec_result.stderr[-300:] if exec_result.stderr else 'None'}"
        )

        report_content = (
            f"# GÖKAI Test Execution Report\n"
            f"- Status: {'PASSED' if passed else 'FAILED'}\n"
            f"- Exit Code: {exec_result.exit_code}\n"
            f"- Duration: {exec_result.duration_ms:.1f}ms\n\n"
            f"## STDOUT\n```\n{exec_result.stdout}\n```\n\n"
            f"## STDERR\n```\n{exec_result.stderr}\n```\n"
        )
        self.tool_registry.fs.write_file("test_run_report.txt", report_content)

        test_art = Artifact(
            project_id=context.project_id,
            task_id=context.task_id,
            type=ArtifactType.TEST_REPORT,
            name="test_run_report.txt",
            path="test_run_report.txt",
            content=report_content,
            created_by=self.name,
            metadata={"exit_code": exec_result.exit_code, "passed": passed, "duration_ms": exec_result.duration_ms}
        )
        artifacts.append(test_art)

        errors = []
        if not passed:
            err_msg = exec_result.stderr.strip() or exec_result.stdout.strip()
            errors.append(f"Test failure (code {exec_result.exit_code}): {err_msg[:600]}")

        return AgentRunResult(
            success=passed,
            agent_name=self.name,
            task_id=context.task_id,
            summary=summary,
            artifacts_created=artifacts,
            errors=errors,
            duration_ms=(time.perf_counter() - start_time) * 1000.0
        )
