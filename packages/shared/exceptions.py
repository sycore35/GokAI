"""
GÖK SYSTEMS TECH — GökAI Core Exception Classes
"""


class GokAIException(Exception):
    """Base exception for all GökAI operations."""
    pass


class SecurityViolationError(GokAIException):
    """Raised when an action violates security constraints."""
    pass


class PathTraversalError(SecurityViolationError):
    """Raised when an operation attempts to escape the project workspace."""
    pass


class ExecutionTimeoutError(GokAIException):
    """Raised when a sandboxed execution exceeds timeout boundaries."""
    pass


class ProviderExhaustedError(GokAIException):
    """Raised when all configured AI model providers fail."""
    pass


class MaxCyclesExceededError(GokAIException):
    """Raised when the self-healing debug cycle exceeds MAX_DEBUG_CYCLES."""
    pass


class SkillNotFoundError(GokAIException):
    """Raised when a requested skill cannot be discovered."""
    pass
