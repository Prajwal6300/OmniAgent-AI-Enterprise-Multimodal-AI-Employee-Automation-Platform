"""
OmniAgent AI — LangGraph Orchestration Graph
Assembles the complete cognitive execution graph connecting all specialists,
reasoning synthesis, approval pauses, verification, and audit.
"""

import time
import uuid
from typing import Any

from langgraph.graph import END, StateGraph

from app.core.logging import logger
from app.orchestration.errors import (
    InvalidApprovalError,
    OrchestrationError,
    RequestCancelledError,
    TenantSecurityViolationError,
)
from app.orchestration.events import EventRecorder, OrchestrationEventType
from app.orchestration.nodes import (
    action_node,
    approval_check_node,
    audit_node,
    authenticate_request_node,
    evaluate_result_node,
    execute_agent_node,
    finalize_node,
    reasoning_node,
    route_request_node,
    supervisor_node,
    validate_context_node,
    verify_node,
)
from app.orchestration.router import (
    route_after_approval_check,
    route_after_evaluate,
    route_after_reasoning,
    route_after_supervisor,
)
from app.orchestration.state import OrchestrationState, UnifiedChatResponse


def build_orchestration_graph():
    """Compiles the primary multi-agent orchestration LangGraph workflow."""
    workflow = StateGraph(OrchestrationState)

    # 1. Add all core nodes
    workflow.add_node("authenticate_request", authenticate_request_node)
    workflow.add_node("validate_context", validate_context_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("route_request", route_request_node)
    workflow.add_node("execute_agent", execute_agent_node)
    workflow.add_node("evaluate_result", evaluate_result_node)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("action", action_node)
    workflow.add_node("approval_check", approval_check_node)
    workflow.add_node("verify", verify_node)
    workflow.add_node("audit", audit_node)
    workflow.add_node("finalize", finalize_node)

    # 2. Define Entry Point
    workflow.set_entry_point("authenticate_request")

    # 3. Add Edges
    workflow.add_edge("authenticate_request", "validate_context")
    workflow.add_edge("validate_context", "supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "route_request": "route_request",
            "finalize": "finalize",
        },
    )

    workflow.add_edge("route_request", "execute_agent")
    workflow.add_edge("execute_agent", "evaluate_result")

    workflow.add_conditional_edges(
        "evaluate_result",
        route_after_evaluate,
        {
            "finalize": "finalize",
            "reasoning": "reasoning",
            "action": "action",
            "route_request": "route_request",
        },
    )

    workflow.add_conditional_edges(
        "reasoning",
        route_after_reasoning,
        {
            "action": "action",
            "finalize": "finalize",
        },
    )

    workflow.add_edge("action", "approval_check")

    workflow.add_conditional_edges(
        "approval_check",
        route_after_approval_check,
        {
            "pause": END,
            "verify": "verify",
        },
    )

    workflow.add_edge("verify", "audit")
    workflow.add_edge("audit", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()


async def run_linear_orchestration(initial_state: OrchestrationState) -> OrchestrationState:
    """Robust fallback pipeline executing nodes sequentially if LangGraph is uncompiled."""
    state = dict(initial_state)

    # 1. Authenticate
    u1 = await authenticate_request_node(state)
    state.update(u1)

    # 2. Validate
    u2 = await validate_context_node(state)
    state.update(u2)

    # 3. Supervisor
    u3 = await supervisor_node(state)
    state.update(u3)

    target = state.get("target_agent", "supervisor")
    if target in ("supervisor", "finalize"):
        u_fin = await finalize_node(state)
        state.update(u_fin)
        return state

    # 4. Route
    u4 = await route_request_node(state)
    state.update(u4)

    # 5. Execute Specialist
    u5 = await execute_agent_node(state)
    state.update(u5)

    # 6. Evaluate
    u6 = await evaluate_result_node(state)
    state.update(u6)

    next_step = state.get("next_step", "finalize")

    # 7. Reasoning if needed
    if next_step == "reasoning":
        u_reason = await reasoning_node(state)
        state.update(u_reason)
        next_step = state.get("next_step", "finalize")

    # 8. Action if needed
    if next_step == "action" or state.get("action_requested"):
        u_act = await action_node(state)
        state.update(u_act)

        u_appr = await approval_check_node(state)
        state.update(u_appr)

        if state.get("status") == "WAITING_FOR_APPROVAL":
            return state

        u_ver = await verify_node(state)
        state.update(u_ver)

        u_aud = await audit_node(state)
        state.update(u_aud)

    # 9. Finalize
    u_fin = await finalize_node(state)
    state.update(u_fin)

    return state


class Orchestrator:
    """
    Unified Orchestrator coordinating full multi-agent lifecycles,
    pause-for-approval state preservation, and cryptographic resume execution.
    """

    _active_states: dict[str, OrchestrationState] = {}
    _compiled_graph: Any = None

    def __init__(self):
        if Orchestrator._compiled_graph is None:
            try:
                Orchestrator._compiled_graph = build_orchestration_graph()
            except Exception as e:
                logger.warning("langgraph_compilation_fallback", error=str(e))
                Orchestrator._compiled_graph = None

    async def execute(
        self,
        message: str,
        organization_id: str,
        user_id: str = "anonymous",
        conversation_id: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
        session: Any = None,
        request_id: str | None = None,
    ) -> OrchestrationState:
        """Executes a full orchestration workflow from user input."""
        req_id = request_id or str(uuid.uuid4())
        conv_id = conversation_id or str(uuid.uuid4())

        initial_state: OrchestrationState = {
            "request_id": req_id,
            "user_id": str(user_id),
            "organization_id": str(organization_id),
            "conversation_id": conv_id,
            "user_message": message,
            "attachments": attachments or [],
            "context": context or {},
            "session": session,
            "start_time": time.time(),
            "step_count": 0,
            "agent_call_count": 0,
            "retry_count": 0,
            "is_cancelled": False,
            "status": "INITIALIZED",
            "pending_approval": False,
            "approval_id": None,
            "action_requested": False,
            "agent_outputs": {},
            "evidence": [],
            "citations": [],
            "conflicts": [],
            "execution_steps": [],
        }

        # Track active state for resume/cancel
        Orchestrator._active_states[req_id] = initial_state

        try:
            if Orchestrator._compiled_graph is not None:
                final_state = await Orchestrator._compiled_graph.ainvoke(initial_state)
            else:
                final_state = await run_linear_orchestration(initial_state)

            Orchestrator._active_states[req_id] = final_state
            return final_state

        except Exception as exc:  # noqa: BLE001
            logger.error("orchestration_unhandled_failure", error=str(exc), request_id=req_id)
            err_state = dict(initial_state)
            err_state["status"] = "FAILED"
            err_state["error"] = str(exc)
            err_state["final_response"] = f"An orchestration error occurred: {exc!s}"
            Orchestrator._active_states[req_id] = err_state
            return err_state

    async def resume(
        self,
        request_id: str,
        approval_id: str,
        organization_id: str,
        user_id: str,
        decision: str = "APPROVED",
        reason: str | None = None,
        session: Any = None,
    ) -> OrchestrationState:
        """Resumes a paused workflow following a verified human approval or rejection."""
        paused_state = Orchestrator._active_states.get(request_id)
        if not paused_state:
            raise OrchestrationError(f"No active or paused workflow found for request_id '{request_id}'.")

        # Tenant boundary check
        if paused_state.get("organization_id") != str(organization_id):
            raise TenantSecurityViolationError("Cannot resume workflow belonging to another organization.")

        if paused_state.get("status") != "WAITING_FOR_APPROVAL":
            raise InvalidApprovalError(f"Workflow is in '{paused_state.get('status')}' state, cannot resume.")

        if decision.upper() == "REJECTED":
            paused_state["status"] = "CANCELLED"
            paused_state["pending_approval"] = False
            paused_state["error"] = f"Action rejected by user: {reason or 'Denied'}"
            paused_state["final_response"] = "The requested enterprise action was rejected by human review."
            return paused_state

        # Update state with approval token and resume execution
        paused_state["approval_id"] = approval_id
        paused_state["pending_approval"] = False
        paused_state["status"] = "RUNNING"
        if session:
            paused_state["session"] = session

        # Execute remaining steps: verify -> audit -> finalize
        u_act = await approval_check_node(paused_state)
        paused_state.update(u_act)

        u_ver = await verify_node(paused_state)
        paused_state.update(u_ver)

        u_aud = await audit_node(paused_state)
        paused_state.update(u_aud)

        u_fin = await finalize_node(paused_state)
        paused_state.update(u_fin)

        Orchestrator._active_states[request_id] = paused_state
        return paused_state

    async def cancel(
        self,
        request_id: str,
        organization_id: str,
        reason: str = "Client requested cancellation",
    ) -> OrchestrationState:
        """Cancels an ongoing or paused orchestration workflow."""
        active = Orchestrator._active_states.get(request_id)
        if not active:
            raise OrchestrationError(f"No active workflow found for request_id '{request_id}'.")

        if active.get("organization_id") != str(organization_id):
            raise TenantSecurityViolationError("Cannot cancel workflow belonging to another organization.")

        active["is_cancelled"] = True
        active["status"] = "CANCELLED"
        active["error"] = reason
        active["final_response"] = f"Execution cancelled: {reason}"
        return active

    def get_state(self, request_id: str) -> OrchestrationState | None:
        """Retrieves live or cached orchestration state."""
        return Orchestrator._active_states.get(request_id)
