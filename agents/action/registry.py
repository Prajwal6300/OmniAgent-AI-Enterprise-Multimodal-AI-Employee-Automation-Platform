"""
OmniAgent AI — Action Agent Registry
Maintains the centralized, explicit allowlist of authorized enterprise actions.
Unknown or unregistered actions are rejected by default.
"""

from typing import Any

from pydantic import BaseModel

from agents.action.exceptions import ActionValidationError
from agents.action.schemas import (
    ActionType,
    CreateReportInput,
    CreateTicketInput,
    RiskLevel,
    SendEmailInput,
    SendNotificationInput,
)


class ActionDefinition:
    """Descriptor defining a registered executable action and its security constraints."""

    def __init__(
        self,
        name: str,
        handler_key: str,
        input_schema: type[BaseModel],
        risk_level: RiskLevel | str,
        approval_required: bool,
        required_permission: str,
        description: str = "",
    ):
        self.name = name.lower()
        self.handler_key = handler_key
        self.input_schema = input_schema
        self.risk_level = RiskLevel(risk_level) if isinstance(risk_level, str) else risk_level
        self.approval_required = approval_required
        self.required_permission = required_permission
        self.description = description

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "handler": self.handler_key,
            "risk": self.risk_level.value,
            "approval_required": self.approval_required,
            "required_permission": self.required_permission,
            "description": self.description,
        }


class ActionRegistry:
    """Central registry enforcing strict deny-by-default action resolution."""

    def __init__(self):
        self._actions: dict[str, ActionDefinition] = {}

    def register(self, definition: ActionDefinition) -> None:
        self._actions[definition.name.lower()] = definition

    def get(self, action_type: str) -> ActionDefinition | None:
        if not action_type:
            return None
        return self._actions.get(action_type.strip().lower())

    def is_registered(self, action_type: str) -> bool:
        return self.get(action_type) is not None

    def validate_action(self, action_type: str) -> ActionDefinition:
        definition = self.get(action_type)
        if not definition:
            raise ActionValidationError(
                f"Action '{action_type}' is unknown or not supported. Denied by default.",
                action_type=action_type
            )
        return definition

    def list_actions(self) -> list[ActionDefinition]:
        return list(self._actions.values())


# Standard registered actions conforming to specification
action_registry = ActionRegistry()

action_registry.register(
    ActionDefinition(
        name=ActionType.SEND_EMAIL.value,
        handler_key="email",
        input_schema=SendEmailInput,
        risk_level=RiskLevel.MEDIUM,
        approval_required=True,
        required_permission="actions.send_email",
        description="Dispatches a verified email message to an internal or designated recipient.",
    )
)

action_registry.register(
    ActionDefinition(
        name=ActionType.SEND_NOTIFICATION.value,
        handler_key="notification",
        input_schema=SendNotificationInput,
        risk_level=RiskLevel.LOW,
        approval_required=False,
        required_permission="actions.send_notification",
        description="Creates an in-app or direct user notification record.",
    )
)

action_registry.register(
    ActionDefinition(
        name=ActionType.CREATE_TICKET.value,
        handler_key="ticket",
        input_schema=CreateTicketInput,
        risk_level=RiskLevel.MEDIUM,
        approval_required=True,
        required_permission="actions.create_ticket",
        description="Creates an authorized maintenance or issue incident ticket.",
    )
)

action_registry.register(
    ActionDefinition(
        name=ActionType.CREATE_REPORT.value,
        handler_key="report",
        input_schema=CreateReportInput,
        risk_level=RiskLevel.LOW,
        approval_required=False,
        required_permission="actions.create_report",
        description="Compiles and stores a structured internal report artifact.",
    )
)

# Backward-compatible dictionary representation
ACTION_REGISTRY = {
    defn.name: {
        "handler": defn.handler_key,
        "risk": defn.risk_level.value.lower(),
        "approval_required": defn.approval_required,
    }
    for defn in action_registry.list_actions()
}
