"""
GÖK SYSTEMS TECH — SQLAlchemy Database Entities
Implements complete persistence layer for GökAI Platform:
Project, Task, TaskStep, AgentRun, Artifact, MemoryEntry, Skill,
ToolCall, TestRun, SecurityFinding, ModelUsage, ActivityLog.
Fully compatible with SQLite and PostgreSQL.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Text,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship
from gokai.apps.backend.app.core.database import Base


def gen_uuid(prefix: str = "") -> str:
    val = uuid.uuid4().hex[:8]
    return f"{prefix}_{val}" if prefix else val


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(32), primary_key=True, default=lambda: gen_uuid("proj"))
    name = Column(String(128), nullable=False)
    description = Column(Text, default="")
    root_path = Column(String(256), nullable=False)
    default_stack = Column(String(64), default="python")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    memories = relationship("MemoryEntry", back_populates="project", cascade="all, delete-orphan")
    activities = relationship("ActivityLog", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(32), primary_key=True, default=lambda: gen_uuid("task"))
    project_id = Column(String(32), ForeignKey("projects.id"), nullable=False)
    user_prompt = Column(Text, nullable=False)
    status = Column(String(32), default="QUEUED")
    priority = Column(Integer, default=1)
    estimated_cost_usd = Column(Float, default=0.0)
    total_tokens = Column(Integer, default=0)
    debug_cycles = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="tasks")
    steps = relationship("TaskStep", back_populates="task", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="task", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="task", cascade="all, delete-orphan")
    test_runs = relationship("TestRun", back_populates="task", cascade="all, delete-orphan")
    security_findings = relationship("SecurityFinding", back_populates="task", cascade="all, delete-orphan")
    tool_calls = relationship("ToolCall", back_populates="task", cascade="all, delete-orphan")
    model_usages = relationship("ModelUsage", back_populates="task", cascade="all, delete-orphan")


class TaskStep(Base):
    __tablename__ = "task_steps"

    id = Column(String(32), primary_key=True, default=lambda: gen_uuid("step"))
    task_id = Column(String(32), ForeignKey("tasks.id"), nullable=False)
    title = Column(String(128), nullable=False)
    assigned_agent = Column(String(32), nullable=False)
    status = Column(String(32), default="QUEUED")
    order_index = Column(Integer, default=0)
    output = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    task = relationship("Task", back_populates="steps")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String(32), primary_key=True, default=lambda: gen_uuid("run"))
    task_id = Column(String(32), ForeignKey("tasks.id"), nullable=False)
    agent_name = Column(String(64), nullable=False)
    status = Column(String(32), default="RUNNING")
    summary = Column(Text, default="")
    duration_ms = Column(Float, default=0.0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    errors = Column(Text, nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    task = relationship("Task", back_populates="agent_runs")


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(String(32), primary_key=True, default=lambda: gen_uuid("art"))
    project_id = Column(String(32), nullable=False)
    task_id = Column(String(32), ForeignKey("tasks.id"), nullable=False)
    type = Column(String(32), nullable=False)
    name = Column(String(128), nullable=False)
    path = Column(String(256), nullable=False)
    content = Column(Text, default="")
    created_by = Column(String(32), default="agent")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    task = relationship("Task", back_populates="artifacts")


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id = Column(String(32), primary_key=True, default=lambda: gen_uuid("mem"))
    project_id = Column(String(32), ForeignKey("projects.id"), nullable=False)
    tier = Column(Integer, nullable=False)  # 1: Facts, 2: Decisions, 3: Evolution, 4: Tasks
    key = Column(String(128), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="memories")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String(32), primary_key=True, default=lambda: gen_uuid("skl"))
    name = Column(String(64), unique=True, nullable=False)
    description = Column(Text, default="")
    when_to_use = Column(Text, default="")
    tags = Column(String(256), default="")
    instructions = Column(Text, default="")
    path = Column(String(256), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id = Column(String(32), primary_key=True, default=lambda: gen_uuid("tool"))
    task_id = Column(String(32), ForeignKey("tasks.id"), nullable=False)
    agent_name = Column(String(64), nullable=False)
    tool_name = Column(String(64), nullable=False)
    arguments = Column(Text, default="")
    output = Column(Text, nullable=True)
    status = Column(String(32), default="SUCCESS")
    duration_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    task = relationship("Task", back_populates="tool_calls")


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(String(32), primary_key=True, default=lambda: gen_uuid("tst"))
    task_id = Column(String(32), ForeignKey("tasks.id"), nullable=False)
    framework = Column(String(32), default="pytest")
    passed = Column(Boolean, default=False)
    exit_code = Column(Integer, default=0)
    duration_ms = Column(Float, default=0.0)
    stdout = Column(Text, default="")
    stderr = Column(Text, default="")
    errors = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    task = relationship("Task", back_populates="test_runs")


class SecurityFinding(Base):
    __tablename__ = "security_findings"

    id = Column(String(32), primary_key=True, default=lambda: gen_uuid("sec"))
    task_id = Column(String(32), ForeignKey("tasks.id"), nullable=False)
    severity = Column(String(16), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    file_path = Column(String(256), nullable=False)
    issue = Column(Text, nullable=False)
    line_number = Column(Integer, nullable=True)
    snippet = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    task = relationship("Task", back_populates="security_findings")


class ModelUsage(Base):
    __tablename__ = "model_usages"

    id = Column(String(32), primary_key=True, default=lambda: gen_uuid("usg"))
    task_id = Column(String(32), ForeignKey("tasks.id"), nullable=False)
    provider = Column(String(32), nullable=False)
    model = Column(String(64), nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    task = relationship("Task", back_populates="model_usages")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(String(32), primary_key=True, default=lambda: gen_uuid("act"))
    project_id = Column(String(32), ForeignKey("projects.id"), nullable=True)
    task_id = Column(String(32), nullable=True)
    actor = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String(16), default="INFO")  # INFO, WARNING, ERROR, SUCCESS
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="activities")


# Backwards compatibility alias for AuditLog
AuditLog = ActivityLog


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(32), primary_key=True, default=lambda: gen_uuid("conv"))
    project_id = Column(String(32), ForeignKey("projects.id"), nullable=True)
    title = Column(String(256), default="New Conversation")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(32), primary_key=True, default=lambda: gen_uuid("cmsg"))
    conversation_id = Column(String(32), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(16), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    attachments_json = Column(Text, default="[]")
    provider = Column(String(32), nullable=True)
    model = Column(String(64), nullable=True)
    tokens = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages")

