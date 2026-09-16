"""
OmniAgent AI — Database Agent Core
High-level orchestrator for enterprise natural language database querying.
"""

import uuid
from typing import Any

from app.core.logging import logger
from sqlalchemy.ext.asyncio import AsyncSession

from agents.database.executor import DatabaseExecutor
from agents.database.graph import build_database_graph
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
from agents.database.schema_registry import SchemaRegistry, schema_registry
from agents.database.schemas import DatabaseResponse
from agents.database.sql_generator import SQLGenerator
from agents.database.sql_guard import SQLGuard
from agents.database.sql_validator import SQLValidator
from agents.database.state import DatabaseState


class DatabaseAgent:
    """
    Enterprise Database Agent for natural-language business queries.
    Enforces strict zero-trust validation, approved schema allowlists,
    parameterized read-only queries, and multi-tenant isolation.
    """

    def __init__(
        self,
        session: AsyncSession | None = None,
        registry: SchemaRegistry | None = None,
        generator: SQLGenerator | None = None,
        validator: SQLValidator | None = None,
        executor: DatabaseExecutor | None = None,
    ):
        self.session = session
        self.registry = registry or schema_registry
        self.generator = generator or SQLGenerator(self.registry)
        self.validator = validator or SQLValidator(self.registry)
        self.executor = executor or DatabaseExecutor(session=session, validator=self.validator)
        self.guard = SQLGuard()  # Preserves backward compatibility
        self.graph = build_database_graph(
            session=self.session,
            registry=self.registry,
            generator=self.generator,
            validator=self.validator,
            executor=self.executor,
        )

    async def _execute_linear_pipeline(self, initial_state: DatabaseState, session: AsyncSession | None = None) -> DatabaseState:
        """
        Robust fallback pipeline runner if LangGraph is unavailable.
        Executes identical workflow semantics and branch checks.
        """
        state = dict(initial_state)

        # 1. validate_request
        r1 = await validate_request_node(state)
        state.update(r1)
        if state.get("status") in ("FAILED_VALIDATION", "READ_ONLY_REFUSAL", "SECURITY_REFUSAL"):
            r_resp = await validate_response_node(state)
            state.update(r_resp)
            return state

        # 2. identify_data_intent
        r2 = await identify_data_intent_node(state)
        state.update(r2)

        # 3. inspect_schema
        r3 = await inspect_schema_node(state, registry=self.registry)
        state.update(r3)
        if state.get("status") == "UNSUPPORTED_DATA":
            r_resp = await validate_response_node(state)
            state.update(r_resp)
            return state

        # 4. generate_query_plan
        r4 = await generate_query_plan_node(state)
        state.update(r4)

        # 5. generate_sql
        r5 = await generate_sql_node(state, generator=self.generator)
        state.update(r5)
        if state.get("status") in ("UNSUPPORTED_DATA", "SQL_GEN_FAILED"):
            r_resp = await validate_response_node(state)
            state.update(r_resp)
            return state

        # 6. validate_sql
        r6 = await validate_sql_node(state, validator=self.validator)
        state.update(r6)
        if state.get("status") == "FAILED_SQL_VALIDATION":
            r_resp = await validate_response_node(state)
            state.update(r_resp)
            return state

        # 7. enforce_tenant_filter
        r7 = await enforce_tenant_filter_node(state)
        state.update(r7)
        if state.get("status") == "FAILED_TENANT_ISOLATION":
            r_resp = await validate_response_node(state)
            state.update(r_resp)
            return state

        # 8. execute_query
        r8 = await execute_query_node(state, executor=self.executor, session=session or self.session)
        state.update(r8)
        if state.get("status") in ("QUERY_TIMEOUT", "EXECUTION_ERROR") or not state.get("query_executed"):
            r_resp = await validate_response_node(state)
            state.update(r_resp)
            return state

        # 9. summarize_results
        r9 = await summarize_results_node(state)
        state.update(r9)

        # 10. validate_response
        r10 = await validate_response_node(state)
        state.update(r10)

        return state

    async def query(
        self,
        question: str,
        organization_id: str,
        user_id: str,
        limit: int | None = None,
        request_id: str | None = None,
        conversation_id: str | None = None,
        session: AsyncSession | None = None,
    ) -> DatabaseResponse:
        """
        Executes end-to-end question processing through the Database Agent workflow.
        Returns a strongly-typed DatabaseResponse object.
        """
        req_id = request_id or str(uuid.uuid4())
        initial_state: DatabaseState = {
            "request_id": req_id,
            "user_id": user_id,
            "organization_id": organization_id,
            "conversation_id": conversation_id or "",
            "question": question,
            "requested_limit": limit,
            "status": "INITIALIZED",
            "query_executed": False,
            "confidence": 0.0,
            "rows": [],
            "result_columns": [],
            "row_count": 0,
            "requires_approval": False,
        }

        logger.info("database_agent_query_started", request_id=req_id, org_id=organization_id)

        try:
            if self.graph is not None:
                final_state = await self.graph.ainvoke(initial_state)
            else:
                final_state = await self._execute_linear_pipeline(initial_state, session=session)
        except Exception as err:  # noqa: BLE001
            logger.error("database_agent_unhandled_error", error=str(err), request_id=req_id)
            final_state = dict(initial_state)
            final_state["error"] = "An unexpected error occurred during database agent execution."
            final_state["summary"] = "An unexpected system error occurred while processing the database query."
            final_state["query_executed"] = False


        return DatabaseResponse(
            question=question,
            summary=final_state.get("summary", "No summary available."),
            columns=final_state.get("result_columns", []),
            rows=final_state.get("rows", []),
            row_count=final_state.get("row_count", 0),
            query_executed=final_state.get("query_executed", False),
            confidence=final_state.get("confidence", 0.0),
            limited=final_state.get("limited", False),
            error=final_state.get("error"),
        )

    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Backward-compatible method for existing pipeline routers.
        """
        question = state.get("question") or state.get("message") or ""
        org_id = state.get("organization_id") or "00000000-0000-0000-0000-000000000001"
        user_id = state.get("user_id") or "00000000-0000-0000-0000-000000000001"

        response = await self.query(
            question=question,
            organization_id=org_id,
            user_id=user_id,
            session=self.session
        )

        return {
            "status": "success" if response.query_executed else "failure",
            "agent": "database",
            "data": response.rows,
            "summary": response.summary,
            "columns": response.columns,
            "row_count": response.row_count,
            "confidence": response.confidence
        }
