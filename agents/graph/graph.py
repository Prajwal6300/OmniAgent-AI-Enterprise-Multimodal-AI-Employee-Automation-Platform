from agents.graph.state import AgentGraphState
from agents.graph.nodes import (
    supervisor_node, vision_node, document_node,
    rag_node, database_node, reasoning_node, action_node
)
from agents.graph.routing import route_next_node

try:
    from langgraph.graph import StateGraph, END
except ImportError:
    StateGraph = None
    END = "__end__"

def build_omniagent_graph():
    if StateGraph is None:
        return None

    workflow = StateGraph(AgentGraphState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("vision", vision_node)
    workflow.add_node("document", document_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("database", database_node)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("action", action_node)

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        route_next_node,
        {
            "vision": "vision",
            "document": "document",
            "rag": "rag",
            "database": "database",
            "reasoning": "reasoning",
            "action": "action",
            "end": END
        }
    )

    for specialist in ["vision", "document", "rag", "database", "reasoning", "action"]:
        workflow.add_edge(specialist, "supervisor")

    return workflow.compile()
