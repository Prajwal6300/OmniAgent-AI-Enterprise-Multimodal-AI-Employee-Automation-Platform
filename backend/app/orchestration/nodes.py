"""
OmniAgent AI — Orchestration LangGraph Nodes
Implements atomic, deterministic node steps for authentication, validation,
supervisor analysis, specialist dispatching, reasoning, approval gating, verification, and audit.
"""

import time
import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.logging import logger
from app.orchestration.errors import (
    InvalidApprovalError,
    RequestCancelledError,
    TenantSecurityViolationError,
    UnauthorizedAgentCallError,
)
from app.orchestration.events import OrchestrationEventType, event_recorder
from app.orchestration.executor import (
    OrchestrationAgentExecutor,
    detect_evidence_conflicts,
)
from app.orchestration.limits import (
    enforce_agent_call_limit,
    enforce_execution_timeout,
    enforce_step_limit,
)
from app.orchestration.policies import SafeTransitionPolicy, SecurityPolicy
from app.orchestration.registry import is_agent_registered, normalize_agent_name
from app.orchestration.state import OrchestrationState

# Shared executor & event recorder
executor = OrchestrationAgentExecutor(event_recorder=event_recorder)


async def authenticate_request_node(state: OrchestrationState) -> dict[str, Any]:
    """Node 1: Authenticates request context and enforces tenant boundary."""
    org_id = state.get("organization_id")
    user_id = state.get("user_id")

    if not org_id or not str(org_id).strip():
        raise TenantSecurityViolationError("Organization ID must be present in authenticated context.")

    req_id = state.get("request_id") or str(uuid.uuid4())
    conv_id = state.get("conversation_id") or str(uuid.uuid4())

    event_recorder.record(
        event_type=OrchestrationEventType.REQUEST_RECEIVED,
        request_id=req_id,
        organization_id=str(org_id),
        conversation_id=conv_id,
        status="RECEIVED",
        metadata={"user_id": str(user_id)},
    )

    return {
        "request_id": req_id,
        "conversation_id": conv_id,
        "start_time": state.get("start_time") or time.time(),
        "step_count": (state.get("step_count") or 0) + 1,
        "agent_call_count": state.get("agent_call_count") or 0,
        "retry_count": state.get("retry_count") or 0,
        "is_cancelled": state.get("is_cancelled") or False,
        "status": "INITIALIZED",
        "current_agent": "start",
        "agent_outputs": state.get("agent_outputs") or {},
        "evidence": state.get("evidence") or [],
        "citations": state.get("citations") or [],
        "conflicts": state.get("conflicts") or [],
        "execution_steps": state.get("execution_steps") or [],
    }


async def validate_context_node(state: OrchestrationState) -> dict[str, Any]:
    """Node 2: Validates untrusted content against prompt injection & checks execution limits."""
    if state.get("is_cancelled"):
        raise RequestCancelledError("Orchestration cancelled by client request.")

    enforce_step_limit(state.get("step_count", 1))
    enforce_execution_timeout(state.get("start_time", time.time()))

    # Zero-trust inspection of user input and context values
    user_msg = state.get("user_message", "")
    SecurityPolicy.inspect_untrusted_text(user_msg)

    ctx = state.get("context") or {}
    for val in ctx.values():
        if isinstance(val, str):
            SecurityPolicy.inspect_untrusted_text(val)

    return {
        "step_count": state["step_count"] + 1,
        "status": "VALIDATED",
    }


async def supervisor_node(state: OrchestrationState) -> dict[str, Any]:
    """Node 3: Supervisor analyzes natural-language request and builds execution plan."""
    if state.get("is_cancelled"):
        raise RequestCancelledError("Orchestration cancelled.")

    enforce_step_limit(state["step_count"])
    enforce_execution_timeout(state["start_time"])

    event_recorder.record(
        event_type=OrchestrationEventType.SUPERVISOR_STARTED,
        request_id=state["request_id"],
        organization_id=state["organization_id"],
        conversation_id=state.get("conversation_id"),
        agent="supervisor",
        status="RUNNING",
    )

    t0 = time.time()
    sup_result = await executor.execute_agent("supervisor", state)
    output = sup_result.get("output", {})
    elapsed_ms = round((time.time() - t0) * 1000, 2)

    selected_agent = output.get("selected_agent", "supervisor")
    canonical_target = normalize_agent_name(selected_agent)
    task_plan = output.get("task_plan", [])
    requires_approval = output.get("requires_approval", False)
    requires_tool = output.get("requires_tool", False)

    steps = list(state.get("execution_steps") or [])
    steps.append({
        "agent": "supervisor",
        "action": f"Selected target agent: {canonical_target}",
        "status": "COMPLETED",
        "timestamp": datetime.now(UTC).isoformat(),
        "duration_ms": elapsed_ms,
        "output_summary": output.get("explanation", ""),
    })

    event_recorder.record(
        event_type=OrchestrationEventType.SUPERVISOR_COMPLETED,
        request_id=state["request_id"],
        organization_id=state["organization_id"],
        conversation_id=state.get("conversation_id"),
        agent="supervisor",
        status="COMPLETED",
        metadata={
            "selected_agent": canonical_target,
            "intent": output.get("intent", ""),
            "requires_approval": requires_approval,
            "elapsed_ms": elapsed_ms,
        },
    )

    # Format plan items
    plan_dicts = [{"step": i + 1, "description": p} for i, p in enumerate(task_plan)]

    return {
        "step_count": state["step_count"] + 1,
        "previous_agent": "supervisor",
        "current_agent": "supervisor",
        "target_agent": canonical_target,
        "intent": output.get("intent", "unknown"),
        "task_type": output.get("task_type", "GENERAL_QUERY"),
        "priority": output.get("priority", "medium"),
        "confidence": output.get("confidence", 1.0),
        "execution_plan": plan_dicts,
        "pending_approval": requires_approval,
        "action_requested": requires_tool or canonical_target == "action_agent",
        "execution_steps": steps,
        "status": "ROUTED",
    }


async def route_request_node(state: OrchestrationState) -> dict[str, Any]:
    """Node 4: Validates agent transitions against safe policy and dispatches."""
    curr = state.get("current_agent", "supervisor")
    target = state.get("target_agent", "supervisor")

    SafeTransitionPolicy.validate_transition(curr, target)

    if not is_agent_registered(target):
        raise UnauthorizedAgentCallError(f"Target agent '{target}' is not registered.")

    return {
        "step_count": state["step_count"] + 1,
        "previous_agent": curr,
        "current_agent": target,
    }


async def execute_agent_node(state: OrchestrationState) -> dict[str, Any]:
    """Node 5: Executes the selected specialist agent."""
    if state.get("is_cancelled"):
        raise RequestCancelledError("Orchestration cancelled.")

    enforce_step_limit(state["step_count"])
    enforce_agent_call_limit(state["agent_call_count"] + 1)
    enforce_execution_timeout(state["start_time"])

    agent_name = state["current_agent"]
    res = await executor.execute_agent(agent_name, state)

    outputs = dict(state.get("agent_outputs") or {})
    outputs[agent_name] = res.get("output", {})

    all_evidence = list(state.get("evidence") or [])
    all_evidence.extend(res.get("evidence", []))

    all_citations = list(state.get("citations") or [])
    all_citations.extend(res.get("citations", []))

    steps = list(state.get("execution_steps") or [])
    steps.append({
        "agent": agent_name,
        "action": f"Executed specialist analysis ({res.get('status')})",
        "status": "COMPLETED" if res.get("status") == "completed" else "FAILED",
        "timestamp": datetime.now(UTC).isoformat(),
        "duration_ms": res.get("elapsed_ms"),
        "output_summary": str(res.get("error") or "Specialist returned data"),
    })

    return {
        "step_count": state["step_count"] + 1,
        "agent_call_count": state["agent_call_count"] + 1,
        "agent_outputs": outputs,
        "evidence": all_evidence,
        "citations": all_citations,
        "execution_steps": steps,
        "status": "AGENT_EXECUTED" if res.get("status") == "completed" else "PARTIAL_SUCCESS",
        "error": res.get("error"),
    }


async def evaluate_result_node(state: OrchestrationState) -> dict[str, Any]:
    """Node 6: Evaluates specialist outputs, detects conflicts, decides if reasoning/action is needed."""
    evidence = state.get("evidence") or []
    conflicts = detect_evidence_conflicts(evidence)

    target_agent = state.get("target_agent", "")
    task_type = state.get("task_type", "")
    state.get("execution_plan") or []

    # Check if action was requested
    action_requested = (
        state.get("action_requested", False)
        or target_agent == "action_agent"
        or "ticket" in state.get("user_message", "").lower()
        or "email" in state.get("user_message", "").lower()
    )

    # Complex requests needing reasoning:
    # 1. More than 1 distinct source type collected
    # 2. Conflicting evidence found
    # 3. Explicit DATA_ANALYSIS / MULTI-AGENT request
    source_types = {e.get("source_type") for e in evidence}
    needs_reasoning = (
        len(source_types) > 1
        or len(conflicts) > 0
        or task_type in ("DATA_ANALYSIS", "IMAGE_ANALYSIS") and "maintenance" in state.get("user_message", "").lower()
        or target_agent == "reasoning_agent"
    )

    next_step = "finalize"
    if action_requested and not state.get("action_result"):
        next_step = "action"
    elif needs_reasoning and "reasoning_agent" not in state.get("agent_outputs", {}):
        next_step = "reasoning"

    return {
        "step_count": state["step_count"] + 1,
        "conflicts": conflicts,
        "next_step": next_step,
        "action_requested": action_requested,
    }


async def reasoning_node(state: OrchestrationState) -> dict[str, Any]:
    """Node 7: Reasoning agent performs multi-source synthesis, conflict reconciliation."""
    if state.get("is_cancelled"):
        raise RequestCancelledError("Orchestration cancelled.")

    enforce_step_limit(state["step_count"])
    enforce_agent_call_limit(state["agent_call_count"] + 1)
    enforce_execution_timeout(state["start_time"])

    event_recorder.record(
        event_type=OrchestrationEventType.REASONING_STARTED,
        request_id=state["request_id"],
        organization_id=state["organization_id"],
        conversation_id=state.get("conversation_id"),
        agent="reasoning_agent",
        status="RUNNING",
    )

    t0 = time.time()
    res = await executor.execute_agent("reasoning_agent", state)
    elapsed_ms = round((time.time() - t0) * 1000, 2)

    outputs = dict(state.get("agent_outputs") or {})
    output_dict = res.get("output", {})
    outputs["reasoning_agent"] = output_dict

    all_evidence = list(state.get("evidence") or [])
    all_evidence.extend(res.get("evidence", []))

    steps = list(state.get("execution_steps") or [])
    steps.append({
        "agent": "reasoning_agent",
        "action": "Grounded multi-source evidence synthesis",
        "status": "COMPLETED",
        "timestamp": datetime.now(UTC).isoformat(),
        "duration_ms": elapsed_ms,
        "output_summary": output_dict.get("answer", "")[:120],
    })

    event_recorder.record(
        event_type=OrchestrationEventType.REASONING_COMPLETED,
        request_id=state["request_id"],
        organization_id=state["organization_id"],
        conversation_id=state.get("conversation_id"),
        agent="reasoning_agent",
        status="COMPLETED",
        metadata={"elapsed_ms": elapsed_ms, "grounded": output_dict.get("grounded", True)},
    )

    next_step = "action" if state.get("action_requested") else "finalize"

    return {
        "step_count": state["step_count"] + 1,
        "agent_call_count": state["agent_call_count"] + 1,
        "agent_outputs": outputs,
        "evidence": all_evidence,
        "execution_steps": steps,
        "final_response": output_dict.get("answer"),
        "confidence": output_dict.get("confidence", 1.0),
        "grounded": output_dict.get("grounded", True),
        "next_step": next_step,
    }


async def action_node(state: OrchestrationState) -> dict[str, Any]:
    """Node 8: Prepares action request, checks risk policy, evaluates approval necessity."""
    from app.agents.action.approval import classify_action_risk, requires_approval
    from app.agents.action.schemas import ActionType

    # Infer action type if not explicitly set
    user_msg = state.get("user_message", "").lower()
    action_type = state.get("action_type")

    if not action_type:
        if "ticket" in user_msg or "maintenance" in user_msg:
            action_type = ActionType.CREATE_TICKET.value
        elif "email" in user_msg or "send report" in user_msg:
            action_type = ActionType.SEND_EMAIL.value
        elif "report" in user_msg:
            action_type = ActionType.CREATE_REPORT.value
        else:
            action_type = ActionType.SEND_NOTIFICATION.value

    # Normalize input
    action_input = dict(state.get("action_input") or {})
    if not action_input:
        if action_type == ActionType.CREATE_TICKET.value:
            action_input = {
                "title": f"Incident Ticket: {user_msg[:60]}",
                "priority": "MEDIUM",
                "description": state.get("final_response") or user_msg,
            }
        elif action_type == ActionType.SEND_EMAIL.value:
            action_input = {
                "recipient": "manager@omniagent.ai",
                "subject": "Automated OmniAgent Intelligence Summary",
                "body": state.get("final_response") or "Analysis completed.",
            }
        elif action_type == ActionType.CREATE_REPORT.value:
            action_input = {
                "title": "Automated Analysis Report",
                "report_type": "INCIDENT_SUMMARY",
                "summary": state.get("final_response") or user_msg,
                "data": {"status": "analyzed"},
            }
        else:
            action_input = {
                "title": "OmniAgent Alert",
                "message": state.get("final_response") or user_msg,
                "channel": "IN_APP",
            }

    risk_level = classify_action_risk(action_type)
    needs_appr = requires_approval(action_type, risk_level)

    event_recorder.record(
        event_type=OrchestrationEventType.ACTION_REQUESTED,
        request_id=state["request_id"],
        organization_id=state["organization_id"],
        conversation_id=state.get("conversation_id"),
        agent="action_agent",
        status="REQUESTED",
        metadata={"action_type": action_type, "risk_level": risk_level.value, "requires_approval": needs_appr},
    )

    return {
        "step_count": state["step_count"] + 1,
        "action_type": action_type,
        "action_input": action_input,
        "pending_approval": needs_appr,
    }


async def approval_check_node(state: OrchestrationState) -> dict[str, Any]:
    """Node 9: Human-in-the-loop gate. Pauses if unapproved, resumes if valid token present."""
    from app.agents.action.approval import (
        compute_payload_hash,
        create_approval_expiry,
        validate_approval_binding,
    )

    needs_appr = state.get("pending_approval", False)
    approval_id = state.get("approval_id")
    action_type = state.get("action_type", "send_notification")
    action_input = state.get("action_input") or {}
    org_id = state["organization_id"]
    user_id = state.get("user_id", "anonymous")

    if needs_appr and not approval_id:
        # Generate approval pause
        appr_id = str(uuid.uuid4())
        payload_hash = compute_payload_hash(
            organization_id=org_id,
            user_id=user_id,
            action_type=action_type,
            normalized_input=action_input,
        )
        expires_at = create_approval_expiry().isoformat()

        approval_detail = {
            "approval_id": appr_id,
            "action_type": action_type,
            "risk_level": "MEDIUM",
            "reason": f"Approval required for enterprise operation '{action_type}'.",
            "payload_summary": f"Target action: {action_type}. Parameters verified.",
            "input_payload": action_input,
            "payload_hash": payload_hash,
            "expires_at": expires_at,
            "created_at": datetime.now(UTC).isoformat(),
        }

        event_recorder.record(
            event_type=OrchestrationEventType.APPROVAL_REQUESTED,
            request_id=state["request_id"],
            organization_id=org_id,
            conversation_id=state.get("conversation_id"),
            agent="action_agent",
            status="WAITING_FOR_APPROVAL",
            metadata={"approval_id": appr_id, "action_type": action_type},
        )

        event_recorder.record(
            event_type=OrchestrationEventType.WORKFLOW_PAUSED,
            request_id=state["request_id"],
            organization_id=org_id,
            conversation_id=state.get("conversation_id"),
            status="PAUSED",
            metadata={"approval_id": appr_id},
        )

        steps = list(state.get("execution_steps") or [])
        steps.append({
            "agent": "action_agent",
            "action": f"PAUSED for human authorization on '{action_type}'",
            "status": "PAUSED",
            "timestamp": datetime.now(UTC).isoformat(),
            "output_summary": f"Approval ID: {appr_id}",
        })

        return {
            "step_count": state["step_count"] + 1,
            "approval_id": appr_id,
            "approval_detail": approval_detail,
            "status": "WAITING_FOR_APPROVAL",
            "pending_approval": True,
            "execution_steps": steps,
        }

    # If approval_id is provided, validate it
    if needs_appr and approval_id:
        stored_detail = state.get("approval_detail") or {}
        stored_hash = stored_detail.get("payload_hash")

        if stored_hash and not validate_approval_binding(
            stored_payload_hash=stored_hash,
            organization_id=org_id,
            user_id=user_id,
            action_type=action_type,
            normalized_input=action_input,
        ):
            raise InvalidApprovalError("INVALID_APPROVAL: Action payload has been modified after approval.")

        event_recorder.record(
            event_type=OrchestrationEventType.APPROVAL_GRANTED,
            request_id=state["request_id"],
            organization_id=org_id,
            conversation_id=state.get("conversation_id"),
            agent="action_agent",
            status="APPROVED",
            metadata={"approval_id": approval_id},
        )

        event_recorder.record(
            event_type=OrchestrationEventType.WORKFLOW_RESUMED,
            request_id=state["request_id"],
            organization_id=org_id,
            conversation_id=state.get("conversation_id"),
            status="RESUMED",
            metadata={"approval_id": approval_id},
        )

    # Execute action immediately
    event_recorder.record(
        event_type=OrchestrationEventType.ACTION_STARTED,
        request_id=state["request_id"],
        organization_id=org_id,
        conversation_id=state.get("conversation_id"),
        agent="action_agent",
        status="RUNNING",
        metadata={"action_type": action_type},
    )

    t0 = time.time()
    action_res = await executor.execute_agent("action_agent", state)
    elapsed_ms = round((time.time() - t0) * 1000, 2)

    output = action_res.get("output", {})
    verified = output.get("verified", False)

    steps = list(state.get("execution_steps") or [])
    steps.append({
        "agent": "action_agent",
        "action": f"Executed '{action_type}'",
        "status": "COMPLETED" if verified else "FAILED",
        "timestamp": datetime.now(UTC).isoformat(),
        "duration_ms": elapsed_ms,
        "output_summary": output.get("message", "Action complete"),
    })

    event_recorder.record(
        event_type=OrchestrationEventType.ACTION_COMPLETED,
        request_id=state["request_id"],
        organization_id=org_id,
        conversation_id=state.get("conversation_id"),
        agent="action_agent",
        status="COMPLETED" if verified else "FAILED",
        metadata={"action_type": action_type, "verified": verified, "elapsed_ms": elapsed_ms},
    )

    return {
        "step_count": state["step_count"] + 1,
        "action_result": output,
        "pending_approval": False,
        "execution_steps": steps,
        "status": "RUNNING",
    }


async def verify_node(state: OrchestrationState) -> dict[str, Any]:
    """Node 10: Verifies execution of actions and ensures state integrity."""
    act_res = state.get("action_result")
    if act_res:
        verified = act_res.get("verified", False)
        event_recorder.record(
            event_type=OrchestrationEventType.ACTION_VERIFIED,
            request_id=state["request_id"],
            organization_id=state["organization_id"],
            conversation_id=state.get("conversation_id"),
            agent="action_agent",
            status="VERIFIED" if verified else "UNVERIFIED",
            metadata={"action_id": act_res.get("action_id"), "verified": verified},
        )

    return {"step_count": state["step_count"] + 1}


async def audit_node(state: OrchestrationState) -> dict[str, Any]:
    """Node 11: Emits persistent audit log entries under authenticated organization."""
    session = state.get("session")
    if session:
        try:
            from uuid import UUID

            from app.services.audit_service import record_audit_log

            org_id = UUID(state["organization_id"])
            user_id = UUID(state["user_id"]) if state.get("user_id") and state["user_id"] != "anonymous" else None
            details = {
                "request_id": state["request_id"],
                "intent": state.get("intent"),
                "status": state.get("status"),
                "step_count": state.get("step_count"),
                "agent_call_count": state.get("agent_call_count"),
            }
            await record_audit_log(
                session=session,
                organization_id=org_id,
                user_id=user_id,
                event_type="ORCHESTRATION_EXECUTION",
                resource_type="orchestration_request",
                resource_id=state["request_id"],
                details=details,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("failed_persisting_audit_log_entry", error=str(exc))

    return {"step_count": state["step_count"] + 1}


async def finalize_node(state: OrchestrationState) -> dict[str, Any]:
    """Node 12: Synthesizes final user-facing response with citations, evidence, and status."""
    if state.get("status") == "WAITING_FOR_APPROVAL":
        # Do not close final response if paused
        return state

    final_resp = state.get("final_response")
    if not final_resp:
        # Check specialist outputs for appropriate primary answer
        outputs = state.get("agent_outputs") or {}
        if "reasoning_agent" in outputs:
            final_resp = outputs["reasoning_agent"].get("answer")
        elif "rag_agent" in outputs:
            final_resp = outputs["rag_agent"].get("answer")
        elif "database_agent" in outputs:
            final_resp = outputs["database_agent"].get("summary")
        elif "vision_agent" in outputs:
            final_resp = outputs["vision_agent"].get("answer") or outputs["vision_agent"].get("summary")
        elif "document_agent" in outputs:
            final_resp = outputs["document_agent"].get("summary")
        elif "action_agent" in outputs:
            final_resp = outputs["action_agent"].get("message")
        else:
            final_resp = "Request analysis completed."

    # If action was completed, append confirmation
    act_res = state.get("action_result")
    if act_res and act_res.get("success"):
        ref = act_res.get("external_reference") or act_res.get("action_id", "")
        final_resp = f"{final_resp}\n\n✓ Action completed: {act_res.get('action_type')} (Ref: {ref})"

    # If conflicts were found, add explicit disclosure
    conflicts = state.get("conflicts") or []
    if conflicts:
        final_resp += "\n\n⚠️ Note: The available sources contain conflicting information regarding this issue."

    status = "COMPLETED"
    if state.get("error") and not final_resp:
        status = "FAILED"
    elif state.get("error"):
        status = "PARTIAL_SUCCESS"

    event_recorder.record(
        event_type=OrchestrationEventType.REQUEST_COMPLETED if status == "COMPLETED" else OrchestrationEventType.REQUEST_FAILED,
        request_id=state["request_id"],
        organization_id=state["organization_id"],
        conversation_id=state.get("conversation_id"),
        status=status,
    )

    steps = list(state.get("execution_steps") or [])
    steps.append({
        "agent": "supervisor",
        "action": f"Finalized orchestration ({status})",
        "status": "COMPLETED",
        "timestamp": datetime.now(UTC).isoformat(),
        "output_summary": "Generated grounded final response.",
    })

    return {
        "step_count": state["step_count"] + 1,
        "final_response": final_resp,
        "status": status,
        "execution_steps": steps,
    }
