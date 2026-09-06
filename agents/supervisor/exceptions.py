from typing import Any

try:
    from app.core.exceptions import BaseAppException
except ImportError:
    class BaseAppException(Exception):  # type: ignore
        def __init__(self, message: str, details: dict[str, Any] | None = None):
            self.message = message
            self.details = details or {}
            super().__init__(self.message)


class SupervisorError(BaseAppException):
    """Base exception for all supervisor agent errors."""


class SupervisorValidationError(SupervisorError):
    """Raised when an incoming user message or payload fails validation."""


class IntentClassificationError(SupervisorError):
    """Raised when intent classification encounters an unrecoverable failure."""


class LLMProviderError(SupervisorError):
    """Raised when the LLM provider fails, times out, or returns invalid payload."""


class DecisionValidationError(SupervisorError):
    """Raised when a generated supervisor decision violates schema or bounds."""
