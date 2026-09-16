"""
GÖK SYSTEMS TECH — Reviewer Agent
Audits project deliverables against user objectives, tests, security audits, and produces
final evidence-based acceptance signoff.
"""

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

logger = get_logger("reviewer_agent")


class ReviewerAgent(BaseAgent):
    """Specialist responsible for final acceptance review and quality signoff."""

    name = "reviewer"
    description = "Quality auditor that evaluates feature completeness, code quality, test verification, and delivery standards."
    permissions = AgentPermissions(can_read_filesystem=True, can_write_filesystem=True)
    allowed_tools = ["read_file", "list_files", "write_file"]

    def get_system_prompt(self, context: TaskContext) -> str:
        return (
            "You are the Executive Code Reviewer & Quality Auditor for GÖK SYSTEMS TECH (GökAI).\n"
            "Review the generated project deliverables against the user's initial objective.\n"
            "Format your structured report as:\n"
            "# GÖKAI Project Acceptance Review\n"
            "## 1. Objective Verification\n"
            "## 2. Architecture & File Structure\n"
            "## 3. Test & Verification Evidence\n"
            "## 4. Security & Quality Assessment\n"
            "## 5. Final Signoff Verdict: [APPROVED / REJECTED]\n"
        )

    async def execute(
        self,
        context: TaskContext,
        input_message: Optional[AgentMessage] = None
    ) -> AgentRunResult:
        start_time = time.perf_counter()
        logger.info(f"ReviewerAgent auditing deliverables for task: {context.task_id}")

        files = self.tool_registry.fs.list_files()
        file_list = "\n".join(f"- {f['path']} ({f['size_bytes']} bytes)" for f in files)

        # Inspect verification files if available
        test_report = ""
        try:
            test_report = self.tool_registry.fs.read_file("test_run_report.txt")
        except Exception:
            test_report = "No automated test report found."

        sec_report = ""
        try:
            sec_report = self.tool_registry.fs.read_file("SECURITY_AUDIT.md")
        except Exception:
            sec_report = "No security audit report found."

        prompt = (
            f"User Objective: {context.user_prompt}\n\n"
            f"Workspace Files:\n{file_list}\n\n"
            f"Test Report Summary:\n{test_report[:800]}\n\n"
            f"Security Audit Summary:\n{sec_report[:800]}\n\n"
            "Perform comprehensive acceptance review and emit the official PROJECT_REVIEW.md report."
        )

        messages = [
            ModelMessage(role="system", content=self.get_system_prompt(context)),
            ModelMessage(role="user", content=prompt),
        ]

        resp = await self.model_router.generate_completion(messages=messages)
        report_content = resp.content

        # Write acceptance report
        self.tool_registry.fs.write_file("PROJECT_REVIEW.md", report_content)

        art = Artifact(
            project_id=context.project_id,
            task_id=context.task_id,
            type=ArtifactType.DOCUMENTATION,
            name="PROJECT_REVIEW.md",
            path="PROJECT_REVIEW.md",
            content=report_content,
            created_by=self.name,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return AgentRunResult(
            success=True,
            agent_name=self.name,
            task_id=context.task_id,
            summary="Completed comprehensive project quality review and emitted signoff report.",
            artifacts_created=[art],
            model_used=f"{resp.provider}:{resp.model}",
            input_tokens=resp.input_tokens,
            output_tokens=resp.output_tokens,
            latency_ms=resp.latency_ms,
            cost_usd=resp.estimated_cost_usd,
            duration_ms=duration_ms
        )
