"""
GÖK SYSTEMS TECH — Task State Machine
Enforces deterministic and valid task status transitions.
"""

from typing import Set, Dict
from gokai.packages.shared.models import TaskStatus
from gokai.packages.shared.exceptions import GokAIException


class InvalidStateTransitionError(GokAIException):
    """Raised when an illegal task state transition is attempted."""
    pass


class TaskStateMachine:
    """Manages legal lifecycle transitions for a GökAI task."""

    ALLOWED_TRANSITIONS: Dict[TaskStatus, Set[TaskStatus]] = {
        TaskStatus.QUEUED: {TaskStatus.PLANNING, TaskStatus.CANCELLED},
        TaskStatus.PLANNING: {TaskStatus.RESEARCHING, TaskStatus.CODING, TaskStatus.FAILED, TaskStatus.CANCELLED},
        TaskStatus.RESEARCHING: {TaskStatus.CODING, TaskStatus.FAILED, TaskStatus.CANCELLED},
        TaskStatus.CODING: {TaskStatus.TESTING, TaskStatus.APPROVAL_PAUSED, TaskStatus.FAILED, TaskStatus.CANCELLED},
        TaskStatus.APPROVAL_PAUSED: {TaskStatus.CODING, TaskStatus.CANCELLED},
        TaskStatus.TESTING: {TaskStatus.REVIEWING, TaskStatus.DEBUGGING, TaskStatus.FAILED, TaskStatus.CANCELLED},
        TaskStatus.DEBUGGING: {TaskStatus.TESTING, TaskStatus.FAILED, TaskStatus.CANCELLED},
        TaskStatus.REVIEWING: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
        TaskStatus.COMPLETED: set(),
        TaskStatus.FAILED: {TaskStatus.QUEUED},  # Allow retry
        TaskStatus.CANCELLED: {TaskStatus.QUEUED},  # Allow retry
    }

    @classmethod
    def can_transition(cls, current: TaskStatus, target: TaskStatus) -> bool:
        return target in cls.ALLOWED_TRANSITIONS.get(current, set())

    @classmethod
    def validate_transition(cls, current: TaskStatus, target: TaskStatus):
        if not cls.can_transition(current, target):
            raise InvalidStateTransitionError(
                f"Illegal state transition: Cannot move task from '{current}' to '{target}'."
            )
