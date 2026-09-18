"""
OmniAgent AI — Reasoning State
Defines the strongly typed LangGraph state dictionary for the Reasoning Agent pipeline.
"""

from typing import Any, TypedDict


class ReasoningState(TypedDict, total=False):
    """
    Strongly typed state dictionary for LangGraph workflow execution.
    Maintains complete execution context, tenant boundaries, normalized evidence,
    and conflict tracking.
    """

    request_id: str
    user_id: str
    organization_id: str
    conversation_id: str

    user_question: str
    task_type: str

    required_agents: list[str]
    execution_plan: list[dict[str, Any]]

    agent_outputs: dict[str, dict[str, Any]]

    evidence: list[dict[str, Any]]
    conflicts: list[dict[str, Any]]

    reasoning_summary: str
    answer: str

    confidence: float
    grounded: bool

    missing_information: list[str]
    contributing_agents: list[str]

    requires_approval: bool

    agent_call_count: int
    depth: int

    context: dict[str, Any]

    status: str
    error: str | None
    latency_ms: float | None
