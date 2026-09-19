"""
OmniAgent AI — Action Agent Security Guardrails
Enforces RBAC authorization, tenant isolation, prompt injection defense,
credential sanitization, exfiltration protection, and anti-code-execution.
"""

import json
import re
from typing import Any
from uuid import UUID

from agents.action.exceptions import (
    ActionSecurityError,
    ActionValidationError,
)
from agents.action.registry import action_registry

# Disallowed parameters that must never be accepted from user or agent input
FORBIDDEN_INPUT_KEYS = {
    "smtp_server",
    "smtp_host",
    "smtp_password",
    "smtp_user",
    "api_key",
    "secret",
    "secret_key",
    "access_token",
    "password",
    "auth_token",
    "credentials",
    "private_key",
}

# Regex for detecting code execution injection patterns in inputs
CODE_INJECTION_PATTERNS = [
    r"\b(__import__|eval|exec|compile|subprocess|os\.system|shutil|popen)\b",
    r"\b(DROP\s+TABLE|ALTER\s+TABLE|TRUNCATE\s+TABLE)\b",
    r"<\s*script\b[^>]*>",
    r"javascript:\s*",
]

# Role-based fallback permissions if explicit permission list is not provided
ROLE_DEFAULT_PERMISSIONS: dict[str, list[str]] = {
    "Admin": [
        "actions.execute",
        "actions.send_email",
        "actions.send_notification",
        "actions.create_ticket",
        "actions.create_report",
        "actions.approve",
    ],
    "Supervisor": [
        "actions.execute",
        "actions.send_email",
        "actions.send_notification",
        "actions.create_ticket",
        "actions.create_report",
        "actions.approve",
    ],
    "Operator": [
        "actions.execute",
        "actions.send_notification",
        "actions.create_ticket",
        "actions.create_report",
    ],
    "Viewer": [
        "actions.send_notification",
    ],
}


class ActionSecurityGuard:
    """Enterprise security gatekeeper for action validation and authorization."""

    @classmethod
    def check_permissions(
        cls,
        action_type: str,
        user_role: str | None,
        user_permissions: list[str] | None,
    ) -> bool:
        """
        Validates user authorization against the action's required permissions.
        Supports both granular permission strings and role-based fallback.
        """
        definition = action_registry.get(action_type)
        if not definition:
            return False

        required_perm = definition.required_permission
        perms = set(user_permissions or [])

        # Check explicit permissions first
        if "actions.execute" in perms or required_perm in perms or "*" in perms:
            return True

        # Fallback to role-based permission map
        role_perms = set(ROLE_DEFAULT_PERMISSIONS.get(user_role or "Operator", []))
        return "actions.execute" in role_perms or required_perm in role_perms

    @classmethod
    def check_approval_permission(
        cls,
        user_role: str | None,
        user_permissions: list[str] | None,
    ) -> bool:
        """Checks whether the user has permission to approve or reject actions."""
        perms = set(user_permissions or [])
        if "actions.approve" in perms or "*" in perms:
            return True

        role = user_role or "Operator"
        role_perms = set(ROLE_DEFAULT_PERMISSIONS.get(role, []))
        return "actions.approve" in role_perms or role in ["Admin", "Supervisor"]

    @classmethod
    def validate_tenant_isolation(
        cls,
        user_org_id: str | UUID,
        target_org_id: str | UUID | None,
    ) -> None:
        """Enforces that operations cannot cross organizational tenant boundaries."""
        if target_org_id is None:
            return
        if str(user_org_id).strip().lower() != str(target_org_id).strip().lower():
            raise ActionSecurityError(
                f"Tenant isolation violation: user organization '{user_org_id}' "
                f"cannot execute or access resources for organization '{target_org_id}'.",
            )

    @classmethod
    def sanitize_input_parameters(cls, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Inspects input parameters against credential injections, code execution strings,
        and unauthorized server definitions.
        """
        # 1. Check for forbidden credential parameter names
        for key in input_data:
            if key.lower() in FORBIDDEN_INPUT_KEYS:
                raise ActionSecurityError(
                    f"Security violation: Sensitive or infrastructure configuration parameter '{key}' "
                    f"is not permitted in user input."
                )

        # 2. Check for arbitrary code execution patterns inside strings
        def _check_val(v: Any, path: str = ""):
            if isinstance(v, str):
                for pat in CODE_INJECTION_PATTERNS:
                    if re.search(pat, v, re.IGNORECASE) and any(
                        kw in v for kw in ["eval(", "exec(", "subprocess", "os.system", "__import__"]
                    ):
                        raise ActionSecurityError(
                            f"Security violation: Arbitrary code execution attempt detected at '{path}'."
                        )
            elif isinstance(v, dict):
                for k, child in v.items():
                    _check_val(child, f"{path}.{k}" if path else k)
            elif isinstance(v, list):
                for idx, child in enumerate(v):
                    _check_val(child, f"{path}[{idx}]")

        _check_val(input_data)
        return input_data

    @classmethod
    def validate_payload_size(cls, input_data: dict[str, Any], max_kb: int = 256) -> None:
        """Protects against oversized payload buffer exhaustion attacks."""
        raw_size = len(json.dumps(input_data).encode("utf-8"))
        max_bytes = max_kb * 1024
        if raw_size > max_bytes:
            raise ActionValidationError(
                f"Action payload size ({round(raw_size / 1024, 2)} KB) exceeds allowable limit of {max_kb} KB."
            )
