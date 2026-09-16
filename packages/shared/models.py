"""
GÖK SYSTEMS TECH — GökAI Shared Data Contracts
Defines foundational Pydantic models, enums, and schemas.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class TaskStatus(str, Enum):
    QUEUED = "QUEUED"
    PLANNING = "PLANNING"
    RESEARCHING = "RESEARCHING"
    CODING = "CODING"
    TESTING = "TESTING"
    DEBUGGING = "DEBUGGING"
    REVIEWING = "REVIEWING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    APPROVAL_PAUSED = "APPROVAL_PAUSED"


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    RESEARCHER = "researcher"
    DEVELOPER = "developer"
    TESTER = "tester"
    DEBUGGER = "debugger"
    DESIGNER = "designer"
    SECURITY = "security"
    DOCUMENTER = "documenter"
    REVIEWER = "reviewer"


class ArtifactType(str, Enum):
    CODE = "code"
    FILE = "file"
    TEST_REPORT = "test_report"
    RESEARCH = "research"
    SECURITY_REPORT = "security_report"
    SCREENSHOT = "screenshot"
    DOCUMENTATION = "documentation"
    LOG = "log"


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: f"art_{uuid.uuid4().hex[:8]}")
    project_id: str
    task_id: str
    type: ArtifactType
    name: str
    path: str
    content: str
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskStep(BaseModel):
    id: str = Field(default_factory=lambda: f"step_{uuid.uuid4().hex[:8]}")
    task_id: str
    title: str
    assigned_agent: AgentRole
    status: TaskStatus = TaskStatus.QUEUED
    order_index: int = 0
    dependencies: List[str] = Field(default_factory=list)
    output: Optional[str] = None
    error: Optional[str] = None


class AgentMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    task_id: str
    project_id: str
    from_agent: str
    to_agent: str
    message_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentRunResult(BaseModel):
    success: bool
    agent_name: str
    task_id: str
    summary: str
    artifacts_created: List[Artifact] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    model_used: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0


class ExecutionResult(BaseModel):
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False


class TaskContext(BaseModel):
    task_id: str
    project_id: str
    user_prompt: str
    workspace_path: str
    current_step: Optional[TaskStep] = None
    facts: List[Dict[str, Any]] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)
    recent_errors: List[str] = Field(default_factory=list)
    active_skills: List[str] = Field(default_factory=list)
