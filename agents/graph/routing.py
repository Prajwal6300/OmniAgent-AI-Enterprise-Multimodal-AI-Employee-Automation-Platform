from agents.graph.state import AgentGraphState

def route_next_node(state: AgentGraphState) -> str:
    next_step = state.get("next_step")
    if next_step in ["vision", "document", "rag", "database", "reasoning", "action"]:
        return next_step
    return "end"
