"""
Tests for TaskStateMachine.
"""

import pytest
from gokai.packages.shared.models import TaskStatus
from gokai.packages.orchestrator.state_machine import TaskStateMachine, InvalidStateTransitionError


def test_state_machine_valid_transitions():
    assert TaskStateMachine.can_transition(TaskStatus.QUEUED, TaskStatus.PLANNING)
    assert TaskStateMachine.can_transition(TaskStatus.PLANNING, TaskStatus.CODING)
    assert TaskStateMachine.can_transition(TaskStatus.CODING, TaskStatus.TESTING)
    assert TaskStateMachine.can_transition(TaskStatus.TESTING, TaskStatus.DEBUGGING)
    assert TaskStateMachine.can_transition(TaskStatus.DEBUGGING, TaskStatus.TESTING)
    assert TaskStateMachine.can_transition(TaskStatus.TESTING, TaskStatus.REVIEWING)
    assert TaskStateMachine.can_transition(TaskStatus.REVIEWING, TaskStatus.COMPLETED)


def test_state_machine_invalid_transitions():
    # Direct jump from QUEUED to COMPLETED is forbidden
    assert not TaskStateMachine.can_transition(TaskStatus.QUEUED, TaskStatus.COMPLETED)

    with pytest.raises(InvalidStateTransitionError):
        TaskStateMachine.validate_transition(TaskStatus.QUEUED, TaskStatus.COMPLETED)
