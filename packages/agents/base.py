"""
GÖK SYSTEMS TECH — Base Agent Contract
Defines the foundation for all specialist AI software engineering workers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from gokai.packages.shared.models import (
    AgentMessage,
    AgentRunResult,
    TaskContext,
    Artifact,
)
from gokai.packages.model_router.router import ModelRouter
from gokai.packages.tools.tool_registry import ToolRegistry


class AgentPermissions(BaseModel):
    can_read_filesystem: bool = True
    can_write_filesystem: bool = False
    can_execute_terminal: bool = False
    can_access_browser: bool = False
    can_make_network_requests: bool = False


class BaseAgent(ABC):
    """Abstract base class for all autonomous engineering agents."""

    name: str
    description: str
    permissions: AgentPermissions
    allowed_tools: List[str]

    def __init__(self, model_router: ModelRouter, tool_registry: ToolRegistry):
        self.model_router = model_router
        self.tool_registry = tool_registry

    @abstractmethod
    def get_system_prompt(self, context: TaskContext) -> str:
        """Returns localized system prompt injected with role and constraints."""
        pass

    @abstractmethod
    async def execute(
        self,
        context: TaskContext,
        input_message: Optional[AgentMessage] = None
    ) -> AgentRunResult:
        """Executes the agent's workflow and returns structured results."""
        pass
