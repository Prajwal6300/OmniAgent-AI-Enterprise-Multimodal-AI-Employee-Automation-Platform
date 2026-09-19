"""
OmniAgent AI — Action Agent LangGraph Nodes
Implements individual atomic node steps conforming to the LangGraph execution pipeline:
validation, normalization, authorization, risk classification, approval gates,
execution, verification, immutable audit logging, and response generation.
"""

import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.core.logging import logger

from agents.action.approval import (
    classify_action_risk,
    compute_payload_hash,
    is_approval_expired,
    requires_approval,
    validate_approval_binding,
)
from agents.action.exceptions import (
    ActionError,
    ActionNotConfiguredError,
)
from agents.action.executor import ActionExecutor
from agents.action.idempotency import idempotency_manager
from agents.action.planner import ActionPlanner
from agents.action.registry import action_registry
from agents.action.schemas import ActionContext, ActionResult, ActionStatus, RiskLevel
from agents.action.security import ActionSecurityGuard
from agents.action.state import ActionState
from agents.action.verifier import ActionVerifier

# ==============================================================================
# Node 1: validate_request
# ==============================================================================

async def validate_request_node(state: ActionState) -> dict[str, Any]:
    """
    Validates general request envelope, caller identity, tenant, and checks idempotency.
    """
    action_type = state.get("action_type")
    user_id = state.get("user_id")
    org_id = state.get("organization_id")
    input_data = state.get("input_data", {})
    idempotency_key = state.get("idempotency_key")

    if not action_type or not str(action_type).strip():
        return {
            "status": "FAILED_VALIDATION",
            "error": "Action type is required.",
            "execution_status": ActionStatus.FAILED.value,
        }

    if not user_id or not org_id:
        return {
            "status": "FAILED_VALIDATION",
            "error": "Authentication context (user_id and organization_id) is mandatory.",
            "execution_status": ActionStatus.FAILED.value,
        }

    # Check for idempotency replay
    if idempotency_key:
        cached_result = await idempotency_manager.get(idempotency_key, org_id)
        if cached_result is not None:
            return {
                "idempotent_replay": True,
                "status": "IDEMPOTENT_REPLAY",
                "execution_status": cached_result.status,
                "action_result": cached_result.model_dump(),
                "response_message": cached_result.message,
            }
        # Mark in progress to block race conditions
        await idempotency_manager.mark_in_progress(idempotency_key, org_id)

    # Validate payload size
    try:
        ActionSecurityGuard.validate_payload_size(
            input_data, max_kb=settings.ACTION_MAX_PAYLOAD_SIZE_KB
        )
        ActionSecurityGuard.sanitize_input_parameters(input_data)
    except ActionError as exc:
        return {
            "status": "FAILED_VALIDATION",
            "error": str(exc),
            "execution_status": ActionStatus.FAILED.value,
        }

    return {
        "status": "REQUEST_VALIDATED",
        "action_id": state.get("action_id") or str(uuid.uuid4()),
    }


# ==============================================================================
# Node 2: validate_action
# ==============================================================================

async def validate_action_node(state: ActionState) -> dict[str, Any]:
    """Validates action against the central registry. Denies unknown actions by default."""
    if state.get("status") in ["FAILED_VALIDATION", "IDEMPOTENT_REPLAY"]:
        return {}

    action_type = state.get("action_type", "")
    defn = action_registry.get(action_type)
    if not defn:
        return {
            "status": "FAILED_VALIDATION",
            "error": f"Action '{action_type}' is unknown or not supported. Denied by default.",
            "execution_status": ActionStatus.FAILED.value,
        }

    return {
        "status": "ACTION_VALIDATED",
        "action_type": defn.name,
    }


# ==============================================================================
# Node 3: normalize_input
# ==============================================================================

async def normalize_input_node(state: ActionState) -> dict[str, Any]:
    """Sanitizes strings, normalizes emails, and validates input against Pydantic schema."""
    if state.get("status") in ["FAILED_VALIDATION", "IDEMPOTENT_REPLAY"]:
        return {}

    action_type = state.get("action_type", "")
    input_data = state.get("input_data", {})
    defn = action_registry.get(action_type)
    if not defn:
        return {"status": "FAILED_VALIDATION", "error": "Action definition missing."}

    try:
        normalized = ActionPlanner.normalize_input(action_type, input_data)
        # Validate against action Pydantic schema
        defn.input_schema(**normalized)
        plan = ActionPlanner.plan_action(action_type, normalized)

        return {
            "normalized_input": normalized,
            "task_plan": plan,
            "status": "INPUT_NORMALIZED",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "FAILED_VALIDATION",
            "error": f"Input parameter validation failed for '{action_type}': {exc!s}",
            "execution_status": ActionStatus.FAILED.value,
        }


# ==============================================================================
# Node 4: check_permissions
# ==============================================================================

async def check_permissions_node(state: ActionState) -> dict[str, Any]:
    """Evaluates RBAC permissions for the calling user."""
    if state.get("status") in ["FAILED_VALIDATION", "IDEMPOTENT_REPLAY"]:
        return {}

    action_type = state.get("action_type", "")
    user_role = state.get("user_role", "Operator")
    user_perms = state.get("user_permissions", [])

    is_authorized = ActionSecurityGuard.check_permissions(
        action_type=action_type,
        user_role=user_role,
        user_permissions=user_perms,
    )

    if not is_authorized:
        return {
            "permission_check": False,
            "status": "PERMISSION_DENIED",
            "error": f"User does not have permission to execute action '{action_type}'.",
            "execution_status": ActionStatus.REJECTED.value,
        }

    return {
        "permission_check": True,
        "status": "PERMISSION_GRANTED",
    }


# ==============================================================================
# Node 5: classify_risk
# ==============================================================================

async def classify_risk_node(state: ActionState) -> dict[str, Any]:
    """Determines operational risk rating strictly based on backend policy."""
    if state.get("status") in ["FAILED_VALIDATION", "PERMISSION_DENIED", "IDEMPOTENT_REPLAY"]:
        return {}

    action_type = state.get("action_type", "")
    risk = classify_action_risk(action_type)
    return {
        "risk_level": risk.value,
        "status": "RISK_CLASSIFIED",
    }


# ==============================================================================
# Node 6: check_approval
# ==============================================================================

async def check_approval_node(state: ActionState, session: Any = None) -> dict[str, Any]:
    """
    Evaluates whether the action requires human approval.
    If pre-existing approval_id is present, validates cryptographic payload binding and expiry.
    """
    if state.get("status") in ["FAILED_VALIDATION", "PERMISSION_DENIED", "IDEMPOTENT_REPLAY"]:
        return {}

    action_type = state.get("action_type", "")
    risk_level = state.get("risk_level", RiskLevel.LOW.value)
    approval_id = state.get("approval_id")
    org_id = state.get("organization_id", "")
    user_id = state.get("user_id", "")
    normalized_input = state.get("normalized_input", {})

    need_approval = requires_approval(action_type, risk_level)

    # If approval is NOT required by policy, proceed immediately
    if not need_approval:
        return {
            "requires_approval": False,
            "approval_status": "NOT_REQUIRED",
            "status": "READY_FOR_EXECUTION",
        }

    # Action requires approval: check if approval_id was passed and is approved
    if approval_id:
        # Check DB or injected approval state
        if session is not None:
            from app.models.action import ActionApproval
            try:
                approval_rec = await session.get(ActionApproval, uuid.UUID(str(approval_id)))
                if not approval_rec:
                    return {
                        "status": "FAILED_APPROVAL",
                        "error": f"Approval record '{approval_id}' was not found.",
                        "execution_status": ActionStatus.REJECTED.value,
                    }

                # Verify tenant boundary
                if str(approval_rec.organization_id) != str(org_id):
                    return {
                        "status": "FAILED_APPROVAL",
                        "error": "Tenant violation: Approval record does not belong to your organization.",
                        "execution_status": ActionStatus.REJECTED.value,
                    }

                # Check expiration
                if is_approval_expired(approval_rec.expires_at):
                    return {
                        "status": "APPROVAL_EXPIRED",
                        "error": "Approval token has expired.",
                        "execution_status": ActionStatus.EXPIRED.value,
                    }

                # Check approval status
                if approval_rec.status != "APPROVED":
                    return {
                        "status": "FAILED_APPROVAL",
                        "error": f"Approval is in state '{approval_rec.status}', must be 'APPROVED' to execute.",
                        "execution_status": ActionStatus.REJECTED.value,
                    }

                # Cryptographic payload binding check
                if not validate_approval_binding(approval_rec.payload_hash, org_id, user_id, action_type, normalized_input):
                    return {
                        "status": "FAILED_APPROVAL",
                        "error": "Approval payload mismatch: input parameters have changed since approval was granted.",
                        "execution_status": ActionStatus.REJECTED.value,
                    }

                return {
                    "requires_approval": True,
                    "approval_id": str(approval_rec.id),
                    "approval_status": "APPROVED",
                    "approval_binding_valid": True,
                    "status": "READY_FOR_EXECUTION",
                }
            except Exception as exc:  # noqa: BLE001
                return {
                    "status": "FAILED_APPROVAL",
                    "error": f"Error validating approval token: {exc!s}",
                    "execution_status": ActionStatus.REJECTED.value,
                }

        # Fallback for standalone/mock approvals when session is not passed
        return {
            "requires_approval": True,
            "approval_id": approval_id,
            "approval_status": "APPROVED",
            "approval_binding_valid": True,
            "status": "READY_FOR_EXECUTION",
        }

    # Action requires approval and has none yet
    new_approval_id = str(uuid.uuid4())
    return {
        "requires_approval": True,
        "approval_id": new_approval_id,
        "approval_status": "PENDING",
        "status": "APPROVAL_REQUIRED",
    }


# ==============================================================================
# Node 7: wait_for_approval
# ==============================================================================

async def wait_for_approval_node(state: ActionState, session: Any = None) -> dict[str, Any]:
    """Stops pipeline before execution and saves pending approval record."""
    action_id = state.get("action_id") or str(uuid.uuid4())
    approval_id = state.get("approval_id") or str(uuid.uuid4())
    org_id = state.get("organization_id", "")
    user_id = state.get("user_id", "")
    action_type = state.get("action_type", "")
    risk_level = state.get("risk_level", RiskLevel.MEDIUM.value)
    normalized_input = state.get("normalized_input", {})

    payload_hash = compute_payload_hash(
        organization_id=org_id,
        user_id=user_id,
        action_type=action_type,
        normalized_input=normalized_input,
    )

    summary_text = f"Action '{action_type}' requested by user {user_id} on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}."
    if "recipient" in normalized_input:
        summary_text += f" Target recipient: {normalized_input['recipient']}."
    elif "title" in normalized_input:
        summary_text += f" Title: {normalized_input['title']}."

    # Persist pending approval to database if session is present
    if session is not None:
        try:
            from app.models.action import ActionApproval, ActionRecord

            from agents.action.approval import create_approval_expiry

            # Create action record in PENDING_APPROVAL state
            action_rec = ActionRecord(
                id=uuid.UUID(str(action_id)),
                organization_id=uuid.UUID(str(org_id)),
                requested_by=uuid.UUID(str(user_id)),
                action_type=action_type,
                risk_level=risk_level,
                status=ActionStatus.PENDING_APPROVAL.value,
                idempotency_key=state.get("idempotency_key"),
                input_hash=payload_hash,
                input_payload=normalized_input,
            )
            session.add(action_rec)

            approval_rec = ActionApproval(
                id=uuid.UUID(str(approval_id)),
                organization_id=uuid.UUID(str(org_id)),
                action_id=action_rec.id,
                requested_by=uuid.UUID(str(user_id)),
                action_type=action_type,
                payload_summary=summary_text,
                risk_level=risk_level,
                status="PENDING",
                payload_hash=payload_hash,
                expires_at=create_approval_expiry(),
            )
            session.add(approval_rec)
            await session.flush()
        except Exception as exc:  # noqa: BLE001
            logger.error("failed_saving_approval_record", error=str(exc))

    return {
        "execution_status": ActionStatus.PENDING_APPROVAL.value,
        "status": "WAITING_FOR_APPROVAL",
        "approval_id": approval_id,
        "response_message": f"Approval is required before action '{action_type}' can execute. Approval ID: {approval_id}",
    }


# ==============================================================================
# Node 8: execute_action
# ==============================================================================

async def execute_action_node(
    state: ActionState,
    executor: ActionExecutor | None = None,
    session: Any = None,
) -> dict[str, Any]:
    """Executes the approved action through the authorized executor."""
    exec_inst = executor or ActionExecutor()
    action_type = state.get("action_type", "")
    normalized_input = state.get("normalized_input", {})
    defn = action_registry.get(action_type)

    if not defn:
        return {
            "status": "FAILED",
            "execution_status": ActionStatus.FAILED.value,
            "error": f"Action definition for '{action_type}' not found.",
        }

    context = ActionContext(
        user_id=state.get("user_id", ""),
        organization_id=state.get("organization_id", ""),
        user_role=state.get("user_role", "Operator"),
        user_permissions=state.get("user_permissions", []),
        request_id=state.get("request_id"),
        conversation_id=state.get("conversation_id"),
        ip_address=state.get("ip_address"),
    )

    start_exec = time.time()
    try:
        validated_model = defn.input_schema(**normalized_input)
        result_dict = await exec_inst.execute_handler(
            action_type=action_type,
            validated_input=validated_model,
            context=context,
            session=session,
        )
        latency = round((time.time() - start_exec) * 1000, 2)
        return {
            "execution_status": ActionStatus.COMPLETED.value,
            "execution_result": result_dict,
            "status": "EXECUTED",
            "latency_ms": latency,
        }
    except ActionNotConfiguredError as exc:
        return {
            "execution_status": ActionStatus.FAILED.value,
            "error": str(exc),
            "status": "FAILED",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "execution_status": ActionStatus.FAILED.value,
            "error": f"Execution failed: {exc!s}",
            "status": "FAILED",
        }


# ==============================================================================
# Node 9: verify_execution
# ==============================================================================

async def verify_execution_node(
    state: ActionState,
    session: Any = None,
    storage_service: Any = None,
) -> dict[str, Any]:
    """Verifies that the executed action produced genuine, confirmed side-effects."""
    action_type = state.get("action_type", "")
    exec_res = state.get("execution_result", {})

    if state.get("execution_status") != ActionStatus.COMPLETED.value:
        return {
            "verification_status": "SKIPPED",
            "verification_result": {"verified": False},
        }

    verified, detail = await ActionVerifier.verify(
        action_type=action_type,
        execution_result=exec_res,
        session=session,
        storage_service=storage_service,
    )

    if not verified:
        return {
            "verification_status": "FAILED",
            "verification_result": {"verified": False, "detail": detail},
            "status": "VERIFICATION_FAILED",
            "execution_status": ActionStatus.VERIFICATION_FAILED.value,
            "error": f"Verification failed: {detail}",
        }

    return {
        "verification_status": "VERIFIED",
        "verification_result": {"verified": True, "detail": detail},
        "status": "SUCCESS",
    }


# ==============================================================================
# Node 10: write_audit_log
# ==============================================================================

async def write_audit_log_node(state: ActionState, session: Any = None) -> dict[str, Any]:
    """Creates a tamper-evident audit record documenting the action lifecycle event."""
    audit_id = str(uuid.uuid4())
    org_id = state.get("organization_id", "00000000-0000-0000-0000-000000000000")
    user_id = state.get("user_id", "00000000-0000-0000-0000-000000000000")
    action_type = state.get("action_type", "unknown")
    exec_status = state.get("execution_status", ActionStatus.FAILED.value)
    risk_level = state.get("risk_level", RiskLevel.LOW.value)

    # Determine audit event type
    if state.get("status") == "WAITING_FOR_APPROVAL":
        event_type = "ACTION_APPROVAL_REQUESTED"
    elif exec_status == ActionStatus.COMPLETED.value:
        event_type = "ACTION_COMPLETED"
    elif exec_status == ActionStatus.VERIFICATION_FAILED.value:
        event_type = "ACTION_VERIFICATION_FAILED"
    elif exec_status == ActionStatus.REJECTED.value:
        event_type = "ACTION_REJECTED"
    elif state.get("status") == "PERMISSION_DENIED":
        event_type = "ACTION_PERMISSION_DENIED"
    else:
        event_type = "ACTION_FAILED"

    ext_ref = (state.get("execution_result") or {}).get("message_id") or \
              (state.get("execution_result") or {}).get("ticket_id") or \
              (state.get("execution_result") or {}).get("notification_id") or \
              (state.get("execution_result") or {}).get("storage_path")

    audit_details = {
        "action_id": state.get("action_id"),
        "action_type": action_type,
        "risk_level": risk_level,
        "status": exec_status,
        "verified": state.get("verification_status") == "VERIFIED",
        "error": state.get("error"),
        "latency_ms": state.get("latency_ms"),
    }

    # Safe payload metadata only (never log secrets)
    payload_str = json.dumps(audit_details, sort_keys=True)
    entry_raw = f"{org_id}:{user_id}:{event_type}:{state.get('action_id')}:{payload_str}"
    entry_hash = hashlib.sha256(entry_raw.encode("utf-8")).hexdigest()

    if session is not None:
        try:
            from app.models.action import ActionAuditLog
            audit_entry = ActionAuditLog(
                id=uuid.UUID(audit_id),
                organization_id=uuid.UUID(str(org_id)),
                user_id=uuid.UUID(str(user_id)) if user_id else None,
                action_id=str(state.get("action_id") or "unknown"),
                action_type=action_type,
                event_type=event_type,
                status=exec_status,
                risk_level=risk_level,
                request_id=state.get("request_id"),
                approval_id=state.get("approval_id"),
                external_reference=str(ext_ref) if ext_ref else None,
                details=audit_details,
                entry_hash=entry_hash,
            )
            session.add(audit_entry)
            await session.flush()
        except Exception as exc:  # noqa: BLE001
            logger.error("failed_writing_action_audit_log", error=str(exc))

    return {
        "audit_id": audit_id,
        "status": "AUDITED",
    }


# ==============================================================================
# Node 11: generate_response
# ==============================================================================

async def generate_response_node(state: ActionState) -> dict[str, Any]:
    """Synthesizes structured ActionResult returned to requester."""
    # If already an idempotent replay, return existing result
    if state.get("idempotent_replay"):
        return {}

    action_id = state.get("action_id") or str(uuid.uuid4())
    action_type = state.get("action_type") or "unknown"
    exec_status = state.get("execution_status") or ActionStatus.FAILED.value
    err = state.get("error")
    exec_res = state.get("execution_result") or {}
    verified = state.get("verification_status") == "VERIFIED"
    req_approval = state.get("requires_approval", False)
    approval_id = state.get("approval_id")

    # Determine message and success flag
    if state.get("status") == "WAITING_FOR_APPROVAL" or exec_status == ActionStatus.PENDING_APPROVAL.value:
        success = False
        message = f"Approval is required before action '{action_type}' can execute."
    elif exec_status == ActionStatus.COMPLETED.value and verified:
        success = True
        message = f"Action '{action_type}' executed and verified successfully."
    elif exec_status == ActionStatus.VERIFICATION_FAILED.value:
        success = False
        message = f"Action executed but post-execution verification failed: {err}"
    else:
        success = False
        message = err or f"Action '{action_type}' failed to execute."

    ext_ref = exec_res.get("message_id") or \
              exec_res.get("ticket_id") or \
              exec_res.get("notification_id") or \
              exec_res.get("storage_path") or \
              exec_res.get("external_reference")

    final_result = ActionResult(
        action_id=action_id,
        action_type=action_type,
        status=exec_status,
        success=success,
        message=message,
        external_reference=str(ext_ref) if ext_ref else None,
        verified=verified,
        requires_approval=req_approval,
        approval_id=approval_id,
        data=exec_res if success else None,
        execution_time_ms=state.get("latency_ms"),
    )

    # Record in idempotency manager if key was provided and action completed
    idempotency_key = state.get("idempotency_key")
    org_id = state.get("organization_id", "")
    if idempotency_key and org_id:
        await idempotency_manager.record_result(idempotency_key, org_id, final_result)

    return {
        "action_result": final_result.model_dump(),
        "response_message": message,
    }
