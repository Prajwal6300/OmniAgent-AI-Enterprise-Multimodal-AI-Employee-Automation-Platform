"""
OmniAgent AI — Orchestration Exceptions
Enterprise error types for multi-agent routing, limits, transitions, and security checks.
"""

class OrchestrationError(Exception):
    """Base exception for all orchestration layer failures."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class MaxStepsExceededError(OrchestrationError):
    """Raised when an orchestration flow exceeds the configured maximum step limit."""
    pass


class MaxAgentCallsExceededError(OrchestrationError):
    """Raised when agent calls exceed the bounded quota."""
    pass


class ExecutionTimeoutError(OrchestrationError):
    """Raised when an orchestration flow or agent step exceeds allowable duration."""
    pass


class UnsafeTransitionError(OrchestrationError):
    """Raised when an unauthorized agent transition or recursive loop is attempted."""
    pass


class InvalidApprovalError(OrchestrationError):
    """Raised when an approval token is expired, mismatched, tampered, or rejected."""
    pass


class RequestCancelledError(OrchestrationError):
    """Raised when an orchestration workflow is aborted via explicit cancellation."""
    pass


class PromptInjectionDetectedError(OrchestrationError):
    """Raised when malicious prompt injection or system override attempts are flagged."""
    pass


class UnauthorizedAgentCallError(OrchestrationError):
    """Raised when an unknown, unauthorized, or prohibited agent is requested."""
    pass


class TenantSecurityViolationError(OrchestrationError):
    """Raised when tenant boundary constraints (e.g. missing or mismatched organization_id) are violated."""
    pass


class ActionExecutionFailedError(OrchestrationError):
    """Raised when an action step fails execution or verification."""
    pass
