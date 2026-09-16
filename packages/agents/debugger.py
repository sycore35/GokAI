"""
GÖK SYSTEMS TECH — Debugger Agent
Analyzes execution errors, tracebacks, and test failures, synthesizes corrective patches,
generates unified diff snapshots, and applies atomic fixes to the codebase.
"""

import difflib
import re
import time
from typing import Optional, List
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

logger = get_logger("debugger_agent")


class DebuggerAgent(BaseAgent):
    """Specialist responsible for diagnosing errors, generating diffs, and applying fixes."""

    name = "debugger"
    description = "Root-cause analyst and repair specialist that fixes failing tests and runtime crashes."
    permissions = AgentPermissions(can_read_filesystem=True, can_write_filesystem=True)
    allowed_tools = ["read_file", "write_file", "list_files", "edit_file"]

    def get_system_prompt(self, context: TaskContext) -> str:
        return (
            "You are the Expert Debugger & Systems Repair Agent for GÖK SYSTEMS TECH (GökAI).\n"
            "Your job is to read error tracebacks and test failures, diagnose the exact root cause, "
            "and output the corrected version of the affected file(s).\n"
            "Output format:\n"
            "=== FILE: path/to/fixed_file.py ===\n"
            "```python\n"
            "[full corrected file content]\n"
            "```\n"
            "Do not output partial snippets or explanations outside the file format.\n"
        )

    async def execute(
        self,
        context: TaskContext,
        input_message: Optional[AgentMessage] = None
    ) -> AgentRunResult:
        start_time = time.perf_counter()
        logger.info(f"DebuggerAgent diagnosing failures for task: {context.task_id}")

        # Gather context: test failure logs + code files
        error_context = "\n".join(context.recent_errors) if context.recent_errors else "No error log provided."
        files = self.tool_registry.fs.list_files()
        code_context = ""
        for f in files:
            if f["path"].endswith((".py", ".js", ".ts")) and not f["is_dir"]:
                try:
                    code_context += f"\nFile: {f['path']}\n```\n{self.tool_registry.fs.read_file(f['path'])}\n```\n"
                except Exception:
                    pass

        prompt = (
            f"Original Objective: {context.user_prompt}\n\n"
            f"Test / Runtime Failures:\n{error_context}\n\n"
            f"Current Workspace Files:\n{code_context}\n\n"
            "Analyze the root cause and provide the complete fixed file(s)."
        )

        messages = [
            ModelMessage(role="system", content=self.get_system_prompt(context)),
            ModelMessage(role="user", content=prompt),
        ]

        resp = await self.model_router.generate_completion(messages=messages)
        content = resp.content

        file_blocks = re.findall(
            r"===\s*FILE:\s*([^\s=]+)\s*===\s*```[a-zA-Z0-9_-]*\n(.*?)\n```",
            content,
            re.DOTALL,
        )

        artifacts: List[Artifact] = []
        diffs: List[str] = []

        for file_path, code_content in file_blocks:
            clean_path = file_path.strip().replace("\\", "/")
            old_content = ""
            try:
                old_content = self.tool_registry.fs.read_file(clean_path)
            except Exception:
                old_content = ""

            new_content = code_content.strip()

            # Compute unified diff snapshot
            file_diff = "".join(difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{clean_path}",
                tofile=f"b/{clean_path}"
            ))
            if file_diff:
                diffs.append(file_diff)

            self.tool_registry.fs.write_file(clean_path, new_content)
            art = Artifact(
                project_id=context.project_id,
                task_id=context.task_id,
                type=ArtifactType.CODE,
                name=clean_path,
                path=clean_path,
                content=new_content,
                created_by=self.name,
                metadata={"action": "debug_patch", "diff": file_diff}
            )
            artifacts.append(art)
            logger.info(f"Debugger patched file: {clean_path}")

        # Persist full patch log if diffs generated
        if diffs:
            full_patch = "\n\n".join(diffs)
            self.tool_registry.fs.write_file("DEBUG_PATCH.diff", full_patch)
            patch_art = Artifact(
                project_id=context.project_id,
                task_id=context.task_id,
                type=ArtifactType.OTHER,
                name="DEBUG_PATCH.diff",
                path="DEBUG_PATCH.diff",
                content=full_patch,
                created_by=self.name,
                metadata={"diff_count": len(diffs)}
            )
            artifacts.append(patch_art)

        summary = f"Applied corrective patch to {len(file_blocks)} file(s) with diff tracking."
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return AgentRunResult(
            success=len(artifacts) > 0,
            agent_name=self.name,
            task_id=context.task_id,
            summary=summary,
            artifacts_created=artifacts,
            errors=[] if artifacts else ["Failed to generate corrective patch."],
            model_used=f"{resp.provider}:{resp.model}",
            input_tokens=resp.input_tokens,
            output_tokens=resp.output_tokens,
            latency_ms=resp.latency_ms,
            cost_usd=resp.estimated_cost_usd,
            duration_ms=duration_ms
        )
