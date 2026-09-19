"""
OmniAgent AI — Action Agent LangGraph Workflow
Compiles the StateGraph topology, conditional branching routes,
and deterministic sequential execution fallback for external action processing.
"""

from typing import Any

from agents.action.executor import ActionExecutor
from agents.action.nodes import (
    check_approval_node,
    check_permissions_node,
    classify_risk_node,
    execute_action_node,
    generate_response_node,
    normalize_input_node,
    validate_action_node,
    validate_request_node,
    verify_execution_node,
    wait_for_approval_node,
    write_audit_log_node,
)
from agents.action.state import ActionState

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:
    StateGraph = None
    START = "__start__"
    END = "__end__"


def route_after_approval_check(state: ActionState) -> str:
    """
    Evaluates whether pipeline routes to execution, halts for human approval,
    or aborts early due to validation/authorization failure.
    """
    status = state.get("status")
    if status in ["FAILED_VALIDATION", "PERMISSION_DENIED", "APPROVAL_EXPIRED", "FAILED_APPROVAL"]:
        return "write_audit_log"

    if state.get("requires_approval") and state.get("approval_status") != "APPROVED":
        return "wait_for_approval"

    return "execute_action"


def route_after_request_validation(state: ActionState) -> str:
    """Branches early if initial envelope validation or idempotency replay occurred."""
    if state.get("idempotent_replay"):
        return "generate_response"
    if state.get("status") == "FAILED_VALIDATION":
        return "write_audit_log"
    return "validate_action"


def build_action_graph(
    executor: ActionExecutor | None = None,
    session: Any = None,
    storage_service: Any = None,
):
    """
    Constructs and compiles the atomic LangGraph workflow for the Action Agent.
    """
    if StateGraph is None:
        return None

    exec_inst = executor or ActionExecutor()

    # Bound node closures
    async def _val_req(state: ActionState) -> dict[str, Any]:
        return await validate_request_node(state)

    async def _val_act(state: ActionState) -> dict[str, Any]:
        return await validate_action_node(state)

    async def _norm_inp(state: ActionState) -> dict[str, Any]:
        return await normalize_input_node(state)

    async def _chk_perm(state: ActionState) -> dict[str, Any]:
        return await check_permissions_node(state)

    async def _cls_risk(state: ActionState) -> dict[str, Any]:
        return await classify_risk_node(state)

    async def _chk_appr(state: ActionState) -> dict[str, Any]:
        return await check_approval_node(state, session=session)

    async def _wait_appr(state: ActionState) -> dict[str, Any]:
        return await wait_for_approval_node(state, session=session)

    async def _exec_act(state: ActionState) -> dict[str, Any]:
        return await execute_action_node(state, executor=exec_inst, session=session)

    async def _ver_exec(state: ActionState) -> dict[str, Any]:
        return await verify_execution_node(
            state, session=session, storage_service=storage_service
        )

    async def _write_aud(state: ActionState) -> dict[str, Any]:
        return await write_audit_log_node(state, session=session)

    async def _gen_resp(state: ActionState) -> dict[str, Any]:
        return await generate_response_node(state)

    workflow = StateGraph(ActionState)

    # 1. Add Nodes
    workflow.add_node("validate_request", _val_req)
    workflow.add_node("validate_action", _val_act)
    workflow.add_node("normalize_input", _norm_inp)
    workflow.add_node("check_permissions", _chk_perm)
    workflow.add_node("classify_risk", _cls_risk)
    workflow.add_node("check_approval", _chk_appr)
    workflow.add_node("wait_for_approval", _wait_appr)
    workflow.add_node("execute_action", _exec_act)
    workflow.add_node("verify_execution", _ver_exec)
    workflow.add_node("write_audit_log", _write_aud)
    workflow.add_node("generate_response", _gen_resp)

    # 2. Add Edges & Conditional Routing
    workflow.add_edge(START, "validate_request")

    workflow.add_conditional_edges(
        "validate_request",
        route_after_request_validation,
        {
            "generate_response": "generate_response",
            "write_audit_log": "write_audit_log",
            "validate_action": "validate_action",
        },
    )

    workflow.add_edge("validate_action", "normalize_input")
    workflow.add_edge("normalize_input", "check_permissions")
    workflow.add_edge("check_permissions", "classify_risk")
    workflow.add_edge("classify_risk", "check_approval")

    workflow.add_conditional_edges(
        "check_approval",
        route_after_approval_check,
        {
            "wait_for_approval": "wait_for_approval",
            "execute_action": "execute_action",
            "write_audit_log": "write_audit_log",
        },
    )

    workflow.add_edge("wait_for_approval", "write_audit_log")
    workflow.add_edge("execute_action", "verify_execution")
    workflow.add_edge("verify_execution", "write_audit_log")
    workflow.add_edge("write_audit_log", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()


async def run_sequential_flow(
    initial_state: ActionState,
    executor: ActionExecutor | None = None,
    session: Any = None,
    storage_service: Any = None,
) -> ActionState:
    """
    Direct sequential execution flow through the identical pipeline sequence.
    Provides bulletproof execution and resilience across all environments.
    """
    state: ActionState = dict(initial_state)  # type: ignore
    exec_inst = executor or ActionExecutor()

    # Step 1: validate_request
    state.update(await validate_request_node(state))
    if state.get("idempotent_replay"):
        return state
    if state.get("status") == "FAILED_VALIDATION":
        state.update(await write_audit_log_node(state, session=session))
        state.update(await generate_response_node(state))
        return state

    # Step 2: validate_action
    state.update(await validate_action_node(state))
    if state.get("status") == "FAILED_VALIDATION":
        state.update(await write_audit_log_node(state, session=session))
        state.update(await generate_response_node(state))
        return state

    # Step 3: normalize_input
    state.update(await normalize_input_node(state))
    if state.get("status") == "FAILED_VALIDATION":
        state.update(await write_audit_log_node(state, session=session))
        state.update(await generate_response_node(state))
        return state

    # Step 4: check_permissions
    state.update(await check_permissions_node(state))
    if state.get("status") == "PERMISSION_DENIED":
        state.update(await write_audit_log_node(state, session=session))
        state.update(await generate_response_node(state))
        return state

    # Step 5: classify_risk
    state.update(await classify_risk_node(state))

    # Step 6: check_approval
    state.update(await check_approval_node(state, session=session))
    if state.get("status") in ["APPROVAL_EXPIRED", "FAILED_APPROVAL"]:
        state.update(await write_audit_log_node(state, session=session))
        state.update(await generate_response_node(state))
        return state

    # Step 7: Conditional branch: wait_for_approval vs execute_action
    if state.get("requires_approval") and state.get("approval_status") != "APPROVED":
        state.update(await wait_for_approval_node(state, session=session))
        state.update(await write_audit_log_node(state, session=session))
        state.update(await generate_response_node(state))
        return state

    # Step 8: execute_action
    state.update(await execute_action_node(state, executor=exec_inst, session=session))

    # Step 9: verify_execution
    state.update(
        await verify_execution_node(
            state, session=session, storage_service=storage_service
        )
    )

    # Step 10: write_audit_log
    state.update(await write_audit_log_node(state, session=session))

    # Step 11: generate_response
    state.update(await generate_response_node(state))

    return state
