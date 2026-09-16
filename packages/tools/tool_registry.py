"""
GÖK SYSTEMS TECH — Central Tool Registry
Dispatches tool invocations with fine-grained permission enforcement and audit logging.
"""

from typing import Dict, Any, Callable, Optional, List
from pathlib import Path
import inspect
from gokai.packages.shared.exceptions import SecurityViolationError
from gokai.packages.shared.logger import get_logger
from gokai.packages.tools.jailed_fs import JailedFileSystem
from gokai.packages.tools.terminal import SandboxedTerminal
from gokai.packages.tools.browser import BrowserTool

logger = get_logger("tool_registry")


class ToolRegistry:
    """Manages available tools and enforces permission rules."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root)
        self.fs = JailedFileSystem(self.workspace_root)
        self.terminal = SandboxedTerminal(self.workspace_root)
        self.browser = BrowserTool()
        self._tools: Dict[str, Callable] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        self._tools["read_file"] = self.fs.read_file
        self._tools["write_file"] = self.fs.write_file
        self._tools["create_file"] = self.fs.create_file
        self._tools["edit_file"] = self.fs.edit_file
        self._tools["rename_file"] = self.fs.rename_file
        self._tools["delete_file"] = self.fs.delete_file
        self._tools["search_files"] = self.fs.search_files
        self._tools["list_files"] = self.fs.list_files
        self._tools["file_exists"] = self.fs.file_exists
        self._tools["execute_command"] = self.terminal.execute_command
        self._tools["verify_page"] = self.browser.open_and_verify

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self._tools

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    async def invoke_tool(self, tool_name: str, agent_name: str, **kwargs) -> Any:
        """Executes a tool with permission check and audit trail."""
        if tool_name not in self._tools:
            raise ValueError(f"Unknown tool: '{tool_name}'")

        # Security check: Mutating source code restrictions
        # Security and Reviewer agents may only write their specific markdown audit reports
        if agent_name in ("researcher",) and tool_name in ("write_file", "create_file", "edit_file", "delete_file", "rename_file"):
            raise SecurityViolationError(f"Agent '{agent_name}' is forbidden from using mutating tool '{tool_name}'.")

        if agent_name in ("security", "reviewer") and tool_name in ("delete_file", "rename_file", "edit_file"):
            raise SecurityViolationError(f"Agent '{agent_name}' is forbidden from mutating project source files.")

        if agent_name in ("researcher", "reviewer", "security") and tool_name == "execute_command":
            raise SecurityViolationError(f"Agent '{agent_name}' is forbidden from executing terminal commands.")

        func = self._tools[tool_name]
        logger.info(f"Agent '{agent_name}' invoking tool '{tool_name}' with args: {list(kwargs.keys())}")

        if inspect.iscoroutinefunction(func):
            return await func(**kwargs)
        return func(**kwargs)
