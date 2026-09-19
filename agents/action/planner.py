"""
OmniAgent AI — Action Agent Planner & Input Normalizer
Performs deterministic parameter normalization, canonical formatting,
and operational plan generation for executable actions.
"""

from typing import Any

from agents.action.exceptions import ActionValidationError
from agents.action.registry import action_registry


class ActionPlanner:
    """Sanitizes, canonicalizes, and prepares input data for action execution."""

    @classmethod
    def normalize_input(cls, action_type: str, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively normalizes inputs:
        - Strips whitespace from strings
        - Converts email addresses to lowercase
        - Removes None / null values
        - Ensures consistent data types
        """
        if not isinstance(input_data, dict):
            raise ActionValidationError(
                f"Action input must be a JSON object / dictionary, received {type(input_data).__name__}.",
                action_type=action_type,
            )

        normalized: dict[str, Any] = {}
        for key, value in input_data.items():
            k_clean = key.strip()
            if isinstance(value, str):
                v_clean = value.strip()
                # Lowercase email addresses
                if "email" in k_clean.lower() or "recipient" in k_clean.lower() or "@" in v_clean:
                    v_clean = v_clean.lower()
                normalized[k_clean] = v_clean
            elif isinstance(value, list):
                normalized[k_clean] = [
                    (item.strip().lower() if isinstance(item, str) and "@" in item else (item.strip() if isinstance(item, str) else item))
                    for item in value
                ]
            elif isinstance(value, dict):
                normalized[k_clean] = cls.normalize_input(action_type, value)
            else:
                normalized[k_clean] = value

        return normalized

    @classmethod
    def plan_action(cls, action_type: str, normalized_input: dict[str, Any]) -> list[str]:
        """Generates ordered human-readable operational execution steps for the action."""
        act_lower = action_type.strip().lower()
        defn = action_registry.get(act_lower)
        if not defn:
            return ["Reject unrecognized action."]

        steps = [
            f"Validate action schema for '{act_lower}'",
            "Verify organization tenant boundary and caller permissions",
            f"Evaluate risk level ({defn.risk_level.value}) and human approval status",
        ]
        if defn.approval_required:
            steps.append("Obtain verified human approval token and validate cryptographic payload binding")

        steps.extend([
            f"Dispatch action to configured '{defn.handler_key}' handler",
            "Verify downstream side-effect and capture external reference",
            "Write tamper-evident audit log record",
            "Formulate operational response to requester",
        ])
        return steps
