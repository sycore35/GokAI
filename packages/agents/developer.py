"""
GÖK SYSTEMS TECH — Developer Agent
Generates production code, scaffolds files, manages imports, and emits code artifacts.
"""

import re
from typing import List, Optional
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

logger = get_logger("developer_agent")


class DeveloperAgent(BaseAgent):
    """Specialist responsible for code creation and file writing."""

    name = "developer"
    description = "Full-stack software developer responsible for generating code and configuration."
    permissions = AgentPermissions(can_read_filesystem=True, can_write_filesystem=True)
    allowed_tools = ["read_file", "write_file", "list_files"]

    def get_system_prompt(self, context: TaskContext) -> str:
        return (
            "You are the Senior Full-Stack Developer Agent for GÖK SYSTEMS TECH (GökAI).\n"
            "Your duty is to produce complete, production-grade, typed, and clean software files.\n"
            "RULES:\n"
            "1. Output complete, working code. Never leave TODOs, stubs, or placeholder comments.\n"
            "2. Format your response strictly as a series of code files using this exact format:\n"
            "=== FILE: relative/path/to/file.ext ===\n"
            "```[language]\n"
            "[complete code content]\n"
            "```\n"
            "3. You can output multiple files in one response.\n"
            "4. Follow Clean Code principles: typed, modular, clear error handling.\n"
        )

    async def execute(
        self,
        context: TaskContext,
        input_message: Optional[AgentMessage] = None
    ) -> AgentRunResult:
        logger.info(f"DeveloperAgent executing task: {context.user_prompt}")

        # Survey existing workspace files
        existing_files = self.tool_registry.fs.list_files()
        existing_tree = "\n".join(f"- {f['path']} ({f['size_bytes']} bytes)" for f in existing_files) or "Empty workspace"

        user_content = (
            f"User Objective: {context.user_prompt}\n\n"
            f"Current Workspace Contents:\n{existing_tree}\n\n"
        )

        if context.recent_errors:
            user_content += f"Recent Errors to address:\n" + "\n".join(context.recent_errors) + "\n\n"

        user_content += "Please generate the necessary code files now."

        messages = [
            ModelMessage(role="system", content=self.get_system_prompt(context)),
            ModelMessage(role="user", content=user_content),
        ]

        # Call AI model
        resp = await self.model_router.generate_completion(messages=messages)
        content = resp.content

        # Parse generated files
        # Pattern: === FILE: <path> === followed by ```language\n<code>\n```
        file_blocks = re.findall(
            r"===\s*FILE:\s*([^\s=]+)\s*===\s*```[a-zA-Z0-9_-]*\n(.*?)\n```",
            content,
            re.DOTALL,
        )

        artifacts: List[Artifact] = []

        if not file_blocks:
            # Fallback parsing: single code block without marker
            single_block = re.search(r"```(?:python|javascript|typescript|html|css)?\n(.*?)\n```", content, re.DOTALL)
            if single_block:
                code = single_block.group(1).strip()
                default_filename = "app.py" if "def " in code or "import " in code else "main.txt"
                file_blocks = [(default_filename, code)]

        for file_path, code_content in file_blocks:
            clean_path = file_path.strip().replace("\\", "/")
            self.tool_registry.fs.write_file(clean_path, code_content.strip())
            art = Artifact(
                project_id=context.project_id,
                task_id=context.task_id,
                type=ArtifactType.CODE,
                name=clean_path,
                path=clean_path,
                content=code_content.strip(),
                created_by=self.name,
            )
            artifacts.append(art)
            logger.info(f"Developer wrote file: {clean_path}")

        summary = f"Generated {len(artifacts)} code file(s) across workspace."

        return AgentRunResult(
            success=len(artifacts) > 0,
            agent_name=self.name,
            task_id=context.task_id,
            summary=summary,
            artifacts_created=artifacts,
            errors=[] if artifacts else ["Model did not produce parseable code file blocks."],
            model_used=f"{resp.provider}:{resp.model}",
            input_tokens=resp.input_tokens,
            output_tokens=resp.output_tokens,
            latency_ms=resp.latency_ms,
            cost_usd=resp.estimated_cost_usd,
        )
