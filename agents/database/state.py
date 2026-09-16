"""
OmniAgent AI — Database Agent State
Defines the strongly typed LangGraph state dictionary for the Database Agent workflow.
"""

from typing import Any, TypedDict


class DatabaseState(TypedDict, total=False):
    request_id: str
    user_id: str
    organization_id: str
    conversation_id: str

    question: str
    intent: str

    schema_context: dict[str, Any]
    query_plan: dict[str, Any]

    sql: str
    parameters: dict[str, Any]

    result_columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int

    summary: str
    confidence: float

    requires_approval: bool
    query_executed: bool
    limited: bool
    requested_limit: int | None

    status: str
    error: str | None
