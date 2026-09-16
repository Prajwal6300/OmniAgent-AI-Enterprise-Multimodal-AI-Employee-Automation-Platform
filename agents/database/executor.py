"""
OmniAgent AI — Database Query Executor
Safely executes validated, read-only parameterized queries with timeouts, row bounds, and serialization.
"""

import asyncio
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.config import settings
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from agents.database.exceptions import (
    DatabaseExecutionError,
    QueryTimeoutError,
    SQLValidationError,
)
from agents.database.sql_validator import SQLValidator


def serialize_value(val: Any) -> Any:
    """Safely normalizes database types (UUID, datetime, Decimal) to JSON-serializable primitives."""
    if isinstance(val, UUID):
        return str(val)
    elif isinstance(val, (datetime, date)):
        return val.isoformat()
    elif isinstance(val, Decimal):
        # Return as float if it has fractional parts, or int if whole
        return float(val) if val % 1 != 0 else int(val)
    elif isinstance(val, bytes):
        return val.hex()
    return val


class DatabaseExecutor:
    """
    Controlled execution engine for SQL SELECT queries.
    Enforces multi-layer safety, timeout boundaries, row limits, and tenant scoping.
    """

    def __init__(
        self,
        session: AsyncSession | None = None,
        validator: SQLValidator | None = None,
        timeout_seconds: int | None = None,
        max_rows: int | None = None,
    ):
        self.session = session
        self.validator = validator or SQLValidator()
        self.timeout_seconds = timeout_seconds or getattr(settings, "DATABASE_AGENT_QUERY_TIMEOUT_SECONDS", 10)
        self.max_rows = max_rows or getattr(settings, "DATABASE_AGENT_MAX_ROWS", 100)

    async def execute(
        self,
        sql: str,
        parameters: dict[str, Any],
        organization_id: str,
        limit: int | None = None,
        session: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Validates, parameters-bounds, executes, and normalizes query results.
        Returns:
            {
                "columns": list[str],
                "rows": list[dict[str, Any]],
                "row_count": int,
                "limited": bool
            }
        """
        # Step 1: Pre-Execution Security & Tenant Isolation Validation
        is_valid, error = self.validator.validate(
            sql=sql,
            parameters=parameters,
            organization_id=organization_id
        )
        if not is_valid:
            logger.warning("database_query_validation_failed", error=error, sql=sql[:100])
            raise SQLValidationError(error or "SQL query validation failed.")

        # Step 2: Enforce parameter-level max limit
        effective_limit = min(limit or self.max_rows, getattr(settings, "DATABASE_AGENT_MAX_LIMIT", 500))
        if "limit" in parameters:
            parameters["limit"] = min(parameters["limit"], effective_limit)

        active_session = session or self.session
        need_session_close = False

        if active_session is None:
            active_session = AsyncSessionLocal()
            need_session_close = True

        try:
            # Step 3: Timed Execution
            async def _run_query():
                stmt = text(sql)
                result = await active_session.execute(stmt, parameters)
                
                # Check if result has rows
                if result.returns_rows:
                    keys = list(result.keys())
                    raw_rows = result.all()
                    
                    limited = len(raw_rows) >= effective_limit
                    normalized_rows: list[dict[str, Any]] = []
                    
                    for row in raw_rows[:effective_limit]:
                        row_dict = {}
                        for idx, key in enumerate(keys):
                            row_dict[key] = serialize_value(row[idx])
                        normalized_rows.append(row_dict)

                    return {
                        "columns": keys,
                        "rows": normalized_rows,
                        "row_count": len(normalized_rows),
                        "limited": limited
                    }
                else:
                    return {
                        "columns": [],
                        "rows": [],
                        "row_count": 0,
                        "limited": False
                    }

            try:
                result_data = await asyncio.wait_for(_run_query(), timeout=self.timeout_seconds)
                return result_data
            except asyncio.TimeoutError:
                logger.error("database_query_timeout", timeout_seconds=self.timeout_seconds, sql=sql[:100])
                raise QueryTimeoutError(f"The query took too long to complete (>{self.timeout_seconds}s). Please narrow the request.")
            except (DBAPIError, SQLAlchemyError) as db_err:
                logger.error("database_execution_failure", error=str(db_err))
                # Never expose raw connection strings, passwords, or internal driver stack traces
                raise DatabaseExecutionError("Database execution error occurred while processing the request.")

        finally:
            if need_session_close:
                await active_session.close()
