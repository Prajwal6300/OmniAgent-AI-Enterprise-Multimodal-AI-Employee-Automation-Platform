from typing import Any

from agents.supervisor.nodes import (
    classify_intent_node,
    create_task_plan_node,
    determine_capability_node,
    determine_risk_node,
    select_agent_node,
    validate_decision_node,
    validate_request_node,
)
from agents.supervisor.providers import BaseLLMProvider
from agents.supervisor.state import SupervisorState

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:
    StateGraph = None
    START = "__start__"
    END = "__end__"


def route_after_validation(state: SupervisorState) -> str:
    """Conditional router determining whether to proceed with classification or shortcut to decision validation."""
    if state.get("status") == "FAILED_VALIDATION":
        return "validate_decision"
    return "classify_intent"


def build_supervisor_graph(provider: BaseLLMProvider = None):
    """
    Constructs and compiles the atomic LangGraph workflow for the Supervisor Agent:
    START -> validate_request -> classify_intent -> determine_capability
          -> select_agent -> determine_risk -> create_task_plan -> validate_decision -> END
    """
    if StateGraph is None:
        return None

    # Custom node wrappers to pass provider if needed
    async def _classify_intent(state: SupervisorState) -> dict[str, Any]:
        return await classify_intent_node(state, provider=provider)

    workflow = StateGraph(SupervisorState)

    # Register individual atomic nodes
    workflow.add_node("validate_request", validate_request_node)
    workflow.add_node("classify_intent", _classify_intent)
    workflow.add_node("determine_capability", determine_capability_node)
    workflow.add_node("select_agent", select_agent_node)
    workflow.add_node("determine_risk", determine_risk_node)
    workflow.add_node("create_task_plan", create_task_plan_node)
    workflow.add_node("validate_decision", validate_decision_node)

    # Set Entry Point
    workflow.add_edge(START, "validate_request")

    # Conditional branch after validation
    workflow.add_conditional_edges(
        "validate_request",
        route_after_validation,
        {
            "classify_intent": "classify_intent",
            "validate_decision": "validate_decision"
        }
    )

    # Sequential progression
    workflow.add_edge("classify_intent", "determine_capability")
    workflow.add_edge("determine_capability", "select_agent")
    workflow.add_edge("select_agent", "determine_risk")
    workflow.add_edge("determine_risk", "create_task_plan")
    workflow.add_edge("create_task_plan", "validate_decision")
    workflow.add_edge("validate_decision", END)

    return workflow.compile()
