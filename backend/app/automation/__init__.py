"""
OmniAgent AI — Automation Engine Package
Enterprise workflow execution engine with deterministic condition operators,
trigger abstractions, step executors, approval pausing, and limit safeguards.
"""

from app.automation.conditions.evaluator import ConditionEvaluator
from app.automation.conditions.operators import OPERATORS
from app.automation.conditions.rules import Rule
from app.automation.engine.engine import WorkflowEngine
from app.automation.engine.executor import StepExecutor
from app.automation.engine.state import StepRunResult, WorkflowRunState
from app.automation.limits import (
    APPROVAL_EXPIRATION_MINUTES,
    WORKFLOW_MAX_EXECUTION_SECONDS,
    WORKFLOW_MAX_STEPS,
)
from app.automation.triggers.base import (
    EventTrigger,
    ManualTrigger,
    ScheduleTrigger,
    Trigger,
)
from app.automation.validator import (
    WorkflowValidationError,
    validate_workflow_definition,
)

__all__ = [
    "APPROVAL_EXPIRATION_MINUTES",
    "OPERATORS",
    "WORKFLOW_MAX_EXECUTION_SECONDS",
    "WORKFLOW_MAX_STEPS",
    "ConditionEvaluator",
    "EventTrigger",
    "ManualTrigger",
    "Rule",
    "ScheduleTrigger",
    "StepExecutor",
    "StepRunResult",
    "Trigger",
    "WorkflowEngine",
    "WorkflowRunState",
    "WorkflowValidationError",
    "validate_workflow_definition",
]
