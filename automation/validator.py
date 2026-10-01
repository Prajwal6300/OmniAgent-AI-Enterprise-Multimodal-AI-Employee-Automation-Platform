"""
OmniAgent AI — Workflow Definition Validator
Validates workflow structures, triggers, steps, actions, and conditions prior to persistence or execution.
Prohibits arbitrary code execution or unlisted agents/actions.
"""

from typing import Any

from automation.conditions.operators import OPERATORS
from automation.limits import WORKFLOW_MAX_STEPS

ALLOWED_TRIGGERS: set[str] = {"MANUAL", "EVENT", "SCHEDULE", "WEBHOOK", "FILE_UPLOAD"}
ALLOWED_STEP_TYPES: set[str] = {"agent", "condition", "approval", "action"}
ALLOWED_AGENTS: set[str] = {
    "supervisor", "vision_agent", "database_agent", "reasoning_agent",
    "rag_agent", "document_agent", "action_agent"
}
ALLOWED_ACTIONS: set[str] = {
    "run_agent", "send_notification", "create_report",
    "create_ticket", "send_email", "request_approval"
}


class WorkflowValidationError(Exception):
    pass


def validate_workflow_definition(definition: dict[str, Any]) -> dict[str, Any]:
    """Strictly validates structured workflow definition JSON."""
    if not isinstance(definition, dict):
        raise WorkflowValidationError("Workflow definition must be a JSON object.")

    # Validate Trigger
    trigger = definition.get("trigger", {})
    if not isinstance(trigger, dict):
        raise WorkflowValidationError("Workflow 'trigger' must be a JSON object.")
    t_type = trigger.get("type", "MANUAL").upper()
    if t_type not in ALLOWED_TRIGGERS:
        raise WorkflowValidationError(
            f"Invalid trigger type '{t_type}'. Allowed triggers: {sorted(ALLOWED_TRIGGERS)}."
        )

    # Validate Steps
    steps = definition.get("steps")
    if steps is None or not isinstance(steps, list):
        raise WorkflowValidationError("Workflow 'steps' must be a list of step objects.")

    if len(steps) > WORKFLOW_MAX_STEPS:
        raise WorkflowValidationError(
            f"Workflow exceeds maximum allowable steps ({len(steps)} > {WORKFLOW_MAX_STEPS})."
        )

    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            raise WorkflowValidationError(f"Step {idx + 1} must be an object.")
        stype = step.get("type", "").lower()
        if stype not in ALLOWED_STEP_TYPES:
            raise WorkflowValidationError(
                f"Step {idx + 1}: Unsupported step type '{stype}'. Allowed: {sorted(ALLOWED_STEP_TYPES)}."
            )

        if stype == "agent":
            ag = step.get("agent", "").lower()
            if ag not in ALLOWED_AGENTS:
                raise WorkflowValidationError(
                    f"Step {idx + 1}: Unauthorized agent '{ag}'. Allowed: {sorted(ALLOWED_AGENTS)}."
                )

        elif stype == "condition":
            op = step.get("operator", "").lower()
            if op not in OPERATORS:
                raise WorkflowValidationError(
                    f"Step {idx + 1}: Unsupported condition operator '{op}'."
                )
            if not step.get("field"):
                raise WorkflowValidationError(f"Step {idx + 1}: Condition missing required 'field'.")

        elif stype == "action":
            act = step.get("action", "").lower()
            if act not in ALLOWED_ACTIONS:
                raise WorkflowValidationError(
                    f"Step {idx + 1}: Unsupported action '{act}'. Allowed: {sorted(ALLOWED_ACTIONS)}."
                )

    return definition
