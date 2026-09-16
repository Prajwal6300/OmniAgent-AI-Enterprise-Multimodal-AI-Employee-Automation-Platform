"""
OmniAgent AI — Database Agent Exceptions
Defines typed, production-grade exception hierarchy for database operations.
"""

from typing import Any


class DatabaseAgentError(Exception):
    """Base exception for all Database Agent errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class RequestValidationError(DatabaseAgentError):
    """Raised when an incoming query request is missing required fields or exceeds constraints."""


class SchemaValidationError(DatabaseAgentError):
    """Raised when a requested table, column, or entity is not in the approved schema allowlist."""


class SQLValidationError(DatabaseAgentError):
    """Raised when generated SQL syntax or structure fails validation."""


class UnsafeSQLError(SQLValidationError):
    """Raised when non-SELECT statements, destructive keywords, injection patterns, or forbidden functions are detected."""


class TenantIsolationError(DatabaseAgentError):
    """Raised when a query attempts cross-tenant access or lacks organization filtering."""


class QueryTimeoutError(DatabaseAgentError):
    """Raised when database query execution exceeds configured timeout limit."""


class DatabaseExecutionError(DatabaseAgentError):
    """Raised when database query execution fails at the SQLAlchemy / DB engine layer."""
