"""
OmniAgent AI — Automation Engine Package
Enterprise workflow execution engine with deterministic condition operators,
trigger abstractions, step executors, approval pausing, and limit safeguards.
"""

from automation.conditions.evaluator import ConditionEvaluator
from automation.conditions.operators import OPERATORS
from automation.conditions.rules import Rule
from automation.engine.engine import WorkflowEngine
from automation.engine.executor import StepExecutor
from automation.engine.state import StepRunResult, WorkflowRunState
from automation.limits import (
    APPROVAL_EXPIRATION_MINUTES,
    WORKFLOW_MAX_EXECUTION_SECONDS,
    WORKFLOW_MAX_STEPS,
)
from automation.triggers.base import (
    EventTrigger,
    ManualTrigger,
    ScheduleTrigger,
    Trigger,
)
from automation.validator import (
    WorkflowValidationError,
    validate_workflow_definition,
)

__all__ = [
    "APPROVAL_EXPIRATION_MINUTES",
    "ConditionEvaluator",
    "EventTrigger",
    "ManualTrigger",
    "OPERATORS",
    "Rule",
    "ScheduleTrigger",
    "StepExecutor",
    "StepRunResult",
    "Trigger",
    "WORKFLOW_MAX_EXECUTION_SECONDS",
    "WORKFLOW_MAX_STEPS",
    "WorkflowEngine",
    "WorkflowRunState",
    "WorkflowValidationError",
    "validate_workflow_definition",
]
