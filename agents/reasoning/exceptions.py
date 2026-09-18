"""
OmniAgent AI — Reasoning Agent Exceptions
Defines domain-specific exceptions for reasoning orchestration, security, and grounding validation.
"""


class ReasoningError(Exception):
    """Base exception for all Reasoning Agent errors."""


class UnsafeAgentCallError(ReasoningError):
    """Raised when an execution plan attempts to invoke an unauthorized or disallowed agent."""


class RecursionDepthExceededError(ReasoningError):
    """Raised when the reasoning graph depth exceeds the configured safety threshold."""


class ExecutionLimitExceededError(ReasoningError):
    """Raised when the maximum number of downstream agent invocations is exceeded."""


class TenantSecurityViolationError(ReasoningError):
    """Raised when an operation attempts cross-tenant access or context tampering."""


class AgentExecutionTimeoutError(ReasoningError):
    """Raised when an individual downstream agent execution exceeds the timeout limit."""


class GroundingValidationError(ReasoningError):
    """Raised when generated deductions contradict or lack grounding in verified evidence."""


class MalformedPlanError(ReasoningError):
    """Raised when an LLM produces an invalid or unparseable execution plan."""
