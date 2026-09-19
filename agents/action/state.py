"""
OmniAgent AI — Action Agent State
Defines the strongly typed LangGraph state dictionary for the Action Agent pipeline.
"""

from typing import Any, TypedDict


class ActionState(TypedDict, total=False):
    """
    Strongly typed state dictionary for LangGraph workflow execution.
    Maintains tenant boundaries, request metadata, validation flags,
    risk evaluation, approval checkpoints, idempotency tokens, and audit trails.
    """

    request_id: str
    user_id: str
    organization_id: str
    user_role: str
    user_permissions: list[str]
    conversation_id: str
    ip_address: str | None

    action_id: str
    action_type: str

    input_data: dict[str, Any]
    normalized_input: dict[str, Any]

    risk_level: str
    requires_approval: bool

    approval_id: str | None
    approval_status: str
    approval_binding_valid: bool

    permission_check: bool

    idempotency_key: str | None
    idempotent_replay: bool

    execution_status: str
    execution_result: dict[str, Any]

    verification_status: str
    verification_result: dict[str, Any]

    audit_id: str

    status: str
    error: str | None
    response_message: str

    action_result: dict[str, Any]
    task_plan: list[str]
    latency_ms: float | None
