"""
OmniAgent AI — Reasoning Agent LangGraph Workflow
Assembles the complete StateGraph topology, conditional routing edges,
and sequential execution fallback for multi-source reasoning.
"""

from typing import Any

from agents.reasoning.executor import AgentExecutor
from agents.reasoning.nodes import (
    calculate_confidence_node,
    classify_reasoning_task_node,
    collect_outputs_node,
    create_execution_plan_node,
    detect_conflicts_node,
    execute_required_agents_node,
    generate_response_node,
    normalize_evidence_node,
    reason_over_evidence_node,
    validate_execution_plan_node,
    validate_grounding_node,
    validate_request_node,
)
from agents.reasoning.providers import BaseReasoningLLMProvider
from agents.reasoning.state import ReasoningState

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:
    StateGraph = None
    START = "__start__"
    END = "__end__"


def route_after_request_validation(state: ReasoningState) -> str:
    """Branches early to response generation if input validation or recursion fails."""
    if state.get("status") != "VALIDATED":
        return "generate_response"
    return "classify_reasoning_task"


def route_after_plan_validation(state: ReasoningState) -> str:
    """Branches early if execution plan violates security allowlists or limits."""
    if state.get("status") != "VALIDATED":
        return "generate_response"
    return "execute_required_agents"


def build_reasoning_graph(
    agent_executor: AgentExecutor | None = None,
    llm_provider: BaseReasoningLLMProvider | None = None,
    max_depth: int = 3,
    max_agent_calls: int = 5,
):
    """
    Constructs and compiles the atomic LangGraph workflow for the Reasoning Agent.
    """
    if StateGraph is None:
        return None

    # Bound node closures for injected components
    async def _validate_req(state: ReasoningState) -> dict[str, Any]:
        return await validate_request_node(state, max_depth=max_depth)

    async def _classify_task(state: ReasoningState) -> dict[str, Any]:
        return await classify_reasoning_task_node(state, llm_provider=llm_provider)

    async def _create_plan(state: ReasoningState) -> dict[str, Any]:
        return await create_execution_plan_node(state, llm_provider=llm_provider)

    async def _validate_plan(state: ReasoningState) -> dict[str, Any]:
        return await validate_execution_plan_node(
            state, max_agent_calls=max_agent_calls
        )

    async def _execute_agents(state: ReasoningState) -> dict[str, Any]:
        return await execute_required_agents_node(state, agent_executor=agent_executor)

    async def _reason_evidence(state: ReasoningState) -> dict[str, Any]:
        return await reason_over_evidence_node(state, llm_provider=llm_provider)

    workflow = StateGraph(ReasoningState)

    # 1. Register Nodes
    workflow.add_node("validate_request", _validate_req)
    workflow.add_node("classify_reasoning_task", _classify_task)
    workflow.add_node("create_execution_plan", _create_plan)
    workflow.add_node("validate_execution_plan", _validate_plan)
    workflow.add_node("execute_required_agents", _execute_agents)
    workflow.add_node("collect_outputs", collect_outputs_node)
    workflow.add_node("normalize_evidence", normalize_evidence_node)
    workflow.add_node("detect_conflicts", detect_conflicts_node)
    workflow.add_node("reason_over_evidence", _reason_evidence)
    workflow.add_node("validate_grounding", validate_grounding_node)
    workflow.add_node("calculate_confidence", calculate_confidence_node)
    workflow.add_node("generate_response", generate_response_node)

    # 2. Wire Edges
    workflow.add_edge(START, "validate_request")

    workflow.add_conditional_edges(
        "validate_request",
        route_after_request_validation,
        {
            "generate_response": "generate_response",
            "classify_reasoning_task": "classify_reasoning_task",
        },
    )

    workflow.add_edge("classify_reasoning_task", "create_execution_plan")
    workflow.add_edge("create_execution_plan", "validate_execution_plan")

    workflow.add_conditional_edges(
        "validate_execution_plan",
        route_after_plan_validation,
        {
            "generate_response": "generate_response",
            "execute_required_agents": "execute_required_agents",
        },
    )

    workflow.add_edge("execute_required_agents", "collect_outputs")
    workflow.add_edge("collect_outputs", "normalize_evidence")
    workflow.add_edge("normalize_evidence", "detect_conflicts")
    workflow.add_edge("detect_conflicts", "reason_over_evidence")
    workflow.add_edge("reason_over_evidence", "validate_grounding")
    workflow.add_edge("validate_grounding", "calculate_confidence")
    workflow.add_edge("calculate_confidence", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()


async def run_sequential_flow(
    initial_state: ReasoningState,
    agent_executor: AgentExecutor | None = None,
    llm_provider: BaseReasoningLLMProvider | None = None,
    max_depth: int = 3,
    max_agent_calls: int = 5,
) -> ReasoningState:
    """
    Direct deterministic execution flow through the identical pipeline sequence.
    Guarantees consistent, rock-solid execution even without compiled LangGraph runtime.
    """
    state: ReasoningState = dict(initial_state)  # type: ignore

    # Step 1: validate_request
    state.update(await validate_request_node(state, max_depth=max_depth))
    if state.get("status") != "VALIDATED":
        state.update(await generate_response_node(state))
        return state

    # Step 2: classify_reasoning_task
    state.update(await classify_reasoning_task_node(state, llm_provider=llm_provider))

    # Step 3: create_execution_plan
    state.update(await create_execution_plan_node(state, llm_provider=llm_provider))

    # Step 4: validate_execution_plan
    state.update(
        await validate_execution_plan_node(state, max_agent_calls=max_agent_calls)
    )
    if state.get("status") != "VALIDATED":
        state.update(await generate_response_node(state))
        return state

    # Step 5: execute_required_agents
    state.update(
        await execute_required_agents_node(state, agent_executor=agent_executor)
    )

    # Step 6: collect_outputs
    state.update(await collect_outputs_node(state))

    # Step 7: normalize_evidence
    state.update(await normalize_evidence_node(state))

    # Step 8: detect_conflicts
    state.update(await detect_conflicts_node(state))

    # Step 9: reason_over_evidence
    state.update(await reason_over_evidence_node(state, llm_provider=llm_provider))

    # Step 10: validate_grounding
    state.update(await validate_grounding_node(state))

    # Step 11: calculate_confidence
    state.update(await calculate_confidence_node(state))

    # Step 12: generate_response
    state.update(await generate_response_node(state))

    return state
