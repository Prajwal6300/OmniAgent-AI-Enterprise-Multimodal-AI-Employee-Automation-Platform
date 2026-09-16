"""
OmniAgent AI — Database Agent LangGraph Workflow
Assembles the atomic nodes into a compiled LangGraph state machine.
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from agents.database.executor import DatabaseExecutor
from agents.database.nodes import (
    enforce_tenant_filter_node,
    execute_query_node,
    generate_query_plan_node,
    generate_sql_node,
    identify_data_intent_node,
    inspect_schema_node,
    summarize_results_node,
    validate_request_node,
    validate_response_node,
    validate_sql_node,
)
from agents.database.schema_registry import SchemaRegistry
from agents.database.sql_generator import SQLGenerator
from agents.database.sql_validator import SQLValidator
from agents.database.state import DatabaseState

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:
    StateGraph = None
    START = "__start__"
    END = "__end__"


# Branching routes
def route_after_request_validation(state: DatabaseState) -> str:
    if state.get("status") in ("FAILED_VALIDATION", "READ_ONLY_REFUSAL", "SECURITY_REFUSAL"):
        return "validate_response"
    return "identify_data_intent"


def route_after_schema_inspection(state: DatabaseState) -> str:
    if state.get("status") == "UNSUPPORTED_DATA":
        return "validate_response"
    return "generate_query_plan"


def route_after_sql_generation(state: DatabaseState) -> str:
    if state.get("status") in ("UNSUPPORTED_DATA", "SQL_GEN_FAILED"):
        return "validate_response"
    return "validate_sql"


def route_after_sql_validation(state: DatabaseState) -> str:
    if state.get("status") == "FAILED_SQL_VALIDATION":
        return "validate_response"
    return "enforce_tenant_filter"


def route_after_tenant_enforcement(state: DatabaseState) -> str:
    if state.get("status") == "FAILED_TENANT_ISOLATION":
        return "validate_response"
    return "execute_query"


def route_after_query_execution(state: DatabaseState) -> str:
    if state.get("status") in ("QUERY_TIMEOUT", "EXECUTION_ERROR") or not state.get("query_executed"):
        return "validate_response"
    return "summarize_results"


def build_database_graph(
    session: AsyncSession | None = None,
    registry: SchemaRegistry | None = None,
    generator: SQLGenerator | None = None,
    validator: SQLValidator | None = None,
    executor: DatabaseExecutor | None = None,
):
    """
    Constructs and compiles the atomic LangGraph workflow for the Database Agent:
    START -> validate_request -> identify_data_intent -> inspect_schema
          -> generate_query_plan -> generate_sql -> validate_sql
          -> enforce_tenant_filter -> execute_query -> summarize_results
          -> validate_response -> END
    """
    if StateGraph is None:
        return None

    workflow = StateGraph(DatabaseState)

    # Node wrappers with bound dependencies
    async def _inspect_schema(state: DatabaseState) -> dict[str, Any]:
        return await inspect_schema_node(state, registry=registry)

    async def _generate_sql(state: DatabaseState) -> dict[str, Any]:
        return await generate_sql_node(state, generator=generator)

    async def _validate_sql(state: DatabaseState) -> dict[str, Any]:
        return await validate_sql_node(state, validator=validator)

    async def _execute_query(state: DatabaseState) -> dict[str, Any]:
        return await execute_query_node(state, executor=executor, session=session)

    # Register nodes
    workflow.add_node("validate_request", validate_request_node)
    workflow.add_node("identify_data_intent", identify_data_intent_node)
    workflow.add_node("inspect_schema", _inspect_schema)
    workflow.add_node("generate_query_plan", generate_query_plan_node)
    workflow.add_node("generate_sql", _generate_sql)
    workflow.add_node("validate_sql", _validate_sql)
    workflow.add_node("enforce_tenant_filter", enforce_tenant_filter_node)
    workflow.add_node("execute_query", _execute_query)
    workflow.add_node("summarize_results", summarize_results_node)
    workflow.add_node("validate_response", validate_response_node)

    # Set Entry Point
    workflow.add_edge(START, "validate_request")

    # Conditional branch after request validation
    workflow.add_conditional_edges(
        "validate_request",
        route_after_request_validation,
        {
            "identify_data_intent": "identify_data_intent",
            "validate_response": "validate_response"
        }
    )

    workflow.add_edge("identify_data_intent", "inspect_schema")

    # Conditional branch after schema inspection
    workflow.add_conditional_edges(
        "inspect_schema",
        route_after_schema_inspection,
        {
            "generate_query_plan": "generate_query_plan",
            "validate_response": "validate_response"
        }
    )

    workflow.add_edge("generate_query_plan", "generate_sql")

    # Conditional branch after SQL generation
    workflow.add_conditional_edges(
        "generate_sql",
        route_after_sql_generation,
        {
            "validate_sql": "validate_sql",
            "validate_response": "validate_response"
        }
    )

    # Conditional branch after SQL validation
    workflow.add_conditional_edges(
        "validate_sql",
        route_after_sql_validation,
        {
            "enforce_tenant_filter": "enforce_tenant_filter",
            "validate_response": "validate_response"
        }
    )

    # Conditional branch after tenant enforcement
    workflow.add_conditional_edges(
        "enforce_tenant_filter",
        route_after_tenant_enforcement,
        {
            "execute_query": "execute_query",
            "validate_response": "validate_response"
        }
    )

    # Conditional branch after execution
    workflow.add_conditional_edges(
        "execute_query",
        route_after_query_execution,
        {
            "summarize_results": "summarize_results",
            "validate_response": "validate_response"
        }
    )

    workflow.add_edge("summarize_results", "validate_response")
    workflow.add_edge("validate_response", END)

    return workflow.compile()
