"""
OmniAgent AI — Action Agent Exceptions
Defines custom exception hierarchy for action validation, security violations,
permission boundaries, approval gates, and execution/verification failures.
"""


class ActionError(Exception):
    """Base exception for all Action Agent operations."""
    def __init__(self, message: str, action_type: str | None = None, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.action_type = action_type
        self.details = details or {}


class ActionValidationError(ActionError):
    """Raised when an action request or input parameters fail schema validation."""


class ActionSecurityError(ActionError):
    """Raised on security violations such as tenant boundary crossings or injection attempts."""


class ActionPermissionDeniedError(ActionSecurityError):
    """Raised when the requesting user lacks required permissions for the action."""


class ActionApprovalRequiredError(ActionError):
    """Raised when an action cannot proceed without explicit human-in-the-loop approval."""
    def __init__(self, message: str, approval_id: str | None = None, action_type: str | None = None, details: dict | None = None):
        super().__init__(message, action_type=action_type, details=details)
        self.approval_id = approval_id


class ActionNotConfiguredError(ActionError):
    """Raised when an integration or provider is missing from deployment configuration."""


class ActionExecutionError(ActionError):
    """Raised when the underlying action provider or handler fails during execution."""


class ActionVerificationError(ActionError):
    """Raised when post-execution verification fails to validate that the side-effect occurred."""


class ActionIdempotencyConflictError(ActionError):
    """Raised when an action with the same idempotency key is already in flight."""


class ActionExpiredError(ActionError):
    """Raised when attempting to execute an action using an expired approval token."""


class ActionNotFoundError(ActionError):
    """Raised when an action or approval ID cannot be resolved."""
