"""
OmniAgent AI — Action Agent Validator
Validates action requests against registration allowlists, Pydantic input schemas,
payload size limits, and security constraints.
"""

from typing import Any

from app.core.config import settings
from pydantic import ValidationError

from agents.action.exceptions import (
    ActionPermissionDeniedError,
    ActionValidationError,
)
from agents.action.registry import ActionDefinition, action_registry
from agents.action.schemas import ActionContext
from agents.action.security import ActionSecurityGuard


class ActionValidator:
    """Validates action parameters, schemas, and security requirements."""

    @classmethod
    def validate_action_type(cls, action_type: str) -> ActionDefinition:
        """Validates that action is registered and supported."""
        if not action_type or not action_type.strip():
            raise ActionValidationError("Action type must not be empty.")
        return action_registry.validate_action(action_type)

    @classmethod
    def validate_input_schema(
        cls,
        definition: ActionDefinition,
        normalized_input: dict[str, Any],
    ) -> Any:
        """
        Validates normalized inputs against the action's registered Pydantic model.
        Returns the parsed and validated Pydantic model instance.
        """
        try:
            schema_cls = definition.input_schema
            parsed_model = schema_cls(**normalized_input)
            return parsed_model
        except ValidationError as exc:
            # Format Pydantic errors into human-readable details
            errors = []
            for err in exc.errors():
                loc = " -> ".join(str(p) for p in err.get("loc", []))
                msg = err.get("msg", "Invalid parameter")
                errors.append(f"{loc}: {msg}")
            raise ActionValidationError(
                f"Validation failed for action '{definition.name}': {'; '.join(errors)}",
                action_type=definition.name,
                details={"errors": exc.errors()},
            ) from exc

    @classmethod
    def validate_security(
        cls,
        action_type: str,
        input_data: dict[str, Any],
        context: ActionContext,
    ) -> None:
        """Executes full suite of security, injection, and authorization checks."""
        # 1. Payload size guard
        ActionSecurityGuard.validate_payload_size(
            input_data, max_kb=settings.ACTION_MAX_PAYLOAD_SIZE_KB
        )

        # 2. Input sanitization (credential and injection check)
        ActionSecurityGuard.sanitize_input_parameters(input_data)

        # 3. RBAC authorization check
        is_permitted = ActionSecurityGuard.check_permissions(
            action_type=action_type,
            user_role=context.user_role,
            user_permissions=context.user_permissions,
        )
        if not is_permitted:
            raise ActionPermissionDeniedError(
                f"User '{context.user_id}' with role '{context.user_role}' does not have permission "
                f"to execute action '{action_type}'.",
                action_type=action_type,
            )
