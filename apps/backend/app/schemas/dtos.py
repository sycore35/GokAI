"""
GÖK SYSTEMS TECH — API Data Transfer Objects (DTOs)
Validated with Pydantic v2.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="")
    default_stack: str = Field(default="python")


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    default_stack: Optional[str] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    root_path: str
    default_stack: str
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    project_id: str
    user_prompt: str = Field(..., min_length=3)
    skip_research: bool = False


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: str
    path: str
    created_by: str
    metadata_json: Optional[str] = "{}"
    created_at: datetime


class TaskStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    assigned_agent: str
    status: str
    order_index: int
    output: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    user_prompt: str
    status: str
    estimated_cost_usd: float
    total_tokens: int = 0
    debug_cycles: int = 0
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    steps: List[TaskStepResponse] = Field(default_factory=list)
    artifacts: List[ArtifactResponse] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    active_providers: List[str]
    docker_available: bool
    workspace_directory: str


class MemoryEntryCreate(BaseModel):
    project_id: str
    tier: int = Field(1, ge=1, le=4)
    key: str
    content: str


class MemoryEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    tier: int
    key: str
    content: str
    created_at: datetime


class SkillCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=64)
    description: str = Field(..., min_length=3)
    when_to_use: str = Field(default="")
    tags: List[str] = Field(default_factory=list)
    instructions: str = Field(default="")


class SkillUpdate(BaseModel):
    description: Optional[str] = None
    when_to_use: Optional[str] = None
    tags: Optional[List[str]] = None
    instructions: Optional[str] = None
    enabled: Optional[bool] = None


class SkillResponse(BaseModel):
    name: str
    description: str
    when_to_use: str = ""
    tags: List[str] = Field(default_factory=list)
    instructions: str = ""
    path: str = ""
    is_builtin: bool = True
    enabled: bool = True


class AgentResponse(BaseModel):
    name: str
    title: str
    role: str
    description: str
    allowed_tools: List[str]
    permissions: Dict[str, bool]
    status: str = "Ready"


class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    actor: str
    action: str
    message: str
    level: str
    timestamp: datetime


class SettingsResponse(BaseModel):
    app_name: str
    app_env: str
    debug: bool
    default_provider: str
    default_model: str
    fallback_provider: str
    fallback_model: str
    autonomy_level: str
    max_debug_cycles: int
    max_agent_calls: int
    max_task_cost_usd: float
    sandbox_backend: str
    sandbox_timeout_seconds: int
    docker_available: bool
    active_providers: List[str]


class SettingsUpdate(BaseModel):
    default_provider: Optional[str] = None
    default_model: Optional[str] = None
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None
    autonomy_level: Optional[str] = None
    max_debug_cycles: Optional[int] = None


class ProviderStatusItem(BaseModel):
    provider: str
    display_name: str
    status: str  # "configured" | "not_configured"
    has_key: bool
    masked_key: str
    active_model: str
    models: List[str]


class ProviderTestRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    model: Optional[str] = None


class ProviderTestResponse(BaseModel):
    success: bool
    message: str
    latency_ms: float = 0.0


class ProviderSaveRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    model: Optional[str] = None


class AttachmentItem(BaseModel):
    name: str
    type: str  # "image" | "code" | "file"
    size_bytes: int = 0
    content: str = ""  # Base64 for images, raw text for code/text


class ConversationCreate(BaseModel):
    title: str = "New Conversation"
    project_id: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    project_id: Optional[str] = None
    title: str
    created_at: datetime
    message_count: int = 0


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    attachments: List[AttachmentItem] = Field(default_factory=list)


class ChatMessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    attachments: List[AttachmentItem] = Field(default_factory=list)
    provider: Optional[str] = None
    model: Optional[str] = None
    created_at: datetime


class DiagnosticsResponse(BaseModel):
    system: Dict[str, Any]
    backend: Dict[str, Any]
    providers: Dict[str, Any]
    sandbox: Dict[str, Any]
    recent_logs: List[Dict[str, Any]]
