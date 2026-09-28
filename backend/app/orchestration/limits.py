"""
OmniAgent AI — Orchestration & Workflow Limits
Enforces centralized execution constraints, timeouts, step caps, and retry ceilings.
"""

import time
from typing import NamedTuple

from app.core.config import settings
from app.orchestration.errors import (
    ExecutionTimeoutError,
    MaxAgentCallsExceededError,
    MaxStepsExceededError,
)


class OrchestrationLimits(NamedTuple):
    max_steps: int
    max_agent_calls: int
    max_execution_seconds: float
    max_retries: int
    workflow_max_steps: int
    workflow_max_execution_seconds: float
    approval_expiration_minutes: int


def get_orchestration_limits() -> OrchestrationLimits:
    """Returns current limits configured via application settings."""
    return OrchestrationLimits(
        max_steps=getattr(settings, "ORCHESTRATION_MAX_STEPS", 20),
        max_agent_calls=getattr(settings, "ORCHESTRATION_MAX_AGENT_CALLS", 10),
        max_execution_seconds=float(getattr(settings, "ORCHESTRATION_MAX_EXECUTION_SECONDS", 120)),
        max_retries=getattr(settings, "ORCHESTRATION_MAX_RETRIES", 2),
        workflow_max_steps=getattr(settings, "WORKFLOW_MAX_STEPS", 30),
        workflow_max_execution_seconds=float(getattr(settings, "WORKFLOW_MAX_EXECUTION_SECONDS", 300)),
        approval_expiration_minutes=getattr(settings, "APPROVAL_EXPIRATION_MINUTES", 30),
    )


def enforce_step_limit(current_step: int, max_steps: int | None = None) -> None:
    limit = max_steps or getattr(settings, "ORCHESTRATION_MAX_STEPS", 20)
    if current_step > limit:
        raise MaxStepsExceededError(
            f"Orchestration step limit exceeded ({current_step} > {limit}). "
            "Execution terminated to protect against infinite routing loops."
        )


def enforce_agent_call_limit(current_calls: int, max_calls: int | None = None) -> None:
    limit = max_calls or getattr(settings, "ORCHESTRATION_MAX_AGENT_CALLS", 10)
    if current_calls > limit:
        raise MaxAgentCallsExceededError(
            f"Specialist agent call limit exceeded ({current_calls} > {limit})."
        )


def enforce_execution_timeout(start_time: float, max_seconds: float | None = None) -> None:
    limit = max_seconds or float(getattr(settings, "ORCHESTRATION_MAX_EXECUTION_SECONDS", 120))
    elapsed = time.time() - start_time
    if elapsed > limit:
        raise ExecutionTimeoutError(
            f"Orchestration execution timed out after {elapsed:.2f}s (max {limit:.1f}s)."
        )
