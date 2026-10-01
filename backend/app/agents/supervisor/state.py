from typing import Any, Literal, TypedDict


class SupervisorState(TypedDict, total=False):
    """Strongly typed state dictionary passed across supervisor LangGraph nodes."""
    request_id: str
    user_id: str
    organization_id: str
    conversation_id: str

    user_message: str

    intent: str
    task_type: str
    capability: str

    selected_agent: str

    priority: Literal["low", "medium", "high"]
    confidence: float

    requires_tool: bool
    requires_approval: bool

    task_plan: list[str]

    context: dict[str, Any]

    status: str
    error: str | None
    explanation: str

    # Latency tracking
    supervisor_latency_ms: float
    llm_latency_ms: float
