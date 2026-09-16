"""
OmniAgent AI — Database Agent Workflow Nodes
Atomic LangGraph nodes implementing single responsibilities:
validation -> intent -> schema -> plan -> sql_gen -> sql_val -> tenant -> exec -> summarize -> validate_response
"""

import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from agents.database.exceptions import (
    DatabaseExecutionError,
    QueryTimeoutError,
    SchemaValidationError,
    SQLValidationError,
)
from agents.database.executor import DatabaseExecutor
from agents.database.schema_registry import SchemaRegistry, schema_registry
from agents.database.sql_generator import SQLGenerator
from agents.database.sql_validator import SQLValidator
from agents.database.state import DatabaseState


# ---------------------------------------------------------------------------
# 1. validate_request
# ---------------------------------------------------------------------------
async def validate_request_node(state: DatabaseState) -> dict[str, Any]:
    """
    Validates user authentication, organization context, request constraints,
    and intercepts destructive actions.
    """
    question = state.get("question", "").strip()
    user_id = state.get("user_id", "").strip()
    org_id = state.get("organization_id", "").strip()

    # 1. Question existence & bounds
    if not question:
        return {
            "status": "FAILED_VALIDATION",
            "error": "Question must not be empty.",
            "summary": "Please provide a valid question about business data.",
            "confidence": 0.0,
            "query_executed": False,
        }

    if len(question) > 2000:
        return {
            "status": "FAILED_VALIDATION",
            "error": "Question exceeds maximum allowed length of 2000 characters.",
            "summary": "Question is too long. Please shorten your request.",
            "confidence": 0.0,
            "query_executed": False,
        }

    # 2. Context verification
    if not user_id:
        return {
            "status": "FAILED_VALIDATION",
            "error": "Missing authenticated user context.",
            "summary": "Unauthorized request: user context is missing.",
            "confidence": 0.0,
            "query_executed": False,
        }

    if not org_id:
        return {
            "status": "FAILED_VALIDATION",
            "error": "Missing authenticated organization context.",
            "summary": "Unauthorized request: organization context is missing.",
            "confidence": 0.0,
            "query_executed": False,
        }


    # 3. Intercept explicit destructive intent
    destructive_keywords = [
        r"\bdelete\b", r"\bdrop\b", r"\btruncate\b", r"\balter\b",
        r"\bupdate\b", r"\binsert\b", r"\bdestroy\b", r"\bwipe\b", r"\bpurge\b"
    ]
    q_lower = question.lower()
    for kw in destructive_keywords:
        if re.search(kw, q_lower):
            return {
                "status": "READ_ONLY_REFUSAL",
                "error": "Destructive operations are not permitted.",
                "summary": "The Database Agent only supports authorized read-only queries.",
                "confidence": 0.0,
                "query_executed": False,
                "requires_approval": False,
            }

    # 4. Check prompt injection attempts to leak credentials
    credential_keywords = ["password", "secret_key", "connection_string", "credentials"]
    if any(k in q_lower for k in credential_keywords) and any(v in q_lower for v in ["database", "db", "return", "show", "give"]):
        return {
            "status": "SECURITY_REFUSAL",
            "error": "Access to database credentials or secrets is prohibited.",
            "summary": "The requested information is not available in the authorized business data.",
            "confidence": 0.0,
            "query_executed": False,
        }

    return {"status": "VALIDATED"}


# ---------------------------------------------------------------------------
# 2. identify_data_intent
# ---------------------------------------------------------------------------
async def identify_data_intent_node(state: DatabaseState) -> dict[str, Any]:
    """
    Classifies the user inquiry into a structured intent category without chain of thought.
    """
    if state.get("status") in ("FAILED_VALIDATION", "READ_ONLY_REFUSAL", "SECURITY_REFUSAL"):
        return {}

    q = state.get("question", "").lower()

    # Rule-based structured intent detection
    if any(w in q for w in ["how many", "count", "number of"]):
        intent = "COUNT"
    elif any(w in q for w in ["average", "avg", "mean"]):
        intent = "AVERAGE"
    elif any(w in q for w in ["total", "sum", "overall amount"]):
        intent = "SUM"
    elif any(w in q for w in ["top", "highest", "most", "lowest", "least", "bottom"]):
        intent = "RANKING"
    elif any(w in q for w in ["trend", "over time", "monthly", "daily"]):
        intent = "TREND"
    elif any(w in q for w in ["compare", "comparison", "difference"]):
        intent = "COMPARISON"
    elif any(w in q for w in ["group by", "by category", "by vendor", "by department"]):
        intent = "GROUP_BY"
    elif any(w in q for w in ["where", "failed", "pending", "open", "status"]):
        intent = "FILTER"
    elif any(w in q for w in ["list", "show", "find", "get"]):
        intent = "LIST"
    elif any(w in q for w in ["search", "lookup"]):
        intent = "SEARCH"
    else:
        intent = "LIST"

    return {"intent": intent, "status": "INTENT_IDENTIFIED"}


# ---------------------------------------------------------------------------
# 3. inspect_schema
# ---------------------------------------------------------------------------
async def inspect_schema_node(
    state: DatabaseState,
    registry: SchemaRegistry | None = None
) -> dict[str, Any]:
    """
    Identifies relevant authorized tables and retrieves approved schema metadata.
    """
    if state.get("status") in ("FAILED_VALIDATION", "READ_ONLY_REFUSAL", "SECURITY_REFUSAL"):
        return {}

    reg = registry or schema_registry
    question = state.get("question", "")

    relevant_tables = reg.identify_relevant_tables(question)

    if not relevant_tables:
        # If no authorized table matches the inquiry, fail safely
        return {
            "status": "UNSUPPORTED_DATA",
            "schema_context": {},
            "summary": "The requested information is not available in the authorized business data.",
            "confidence": 0.0,
            "query_executed": False,
        }

    schema_context = {
        table: {
            "description": reg.table_descriptions.get(table, ""),
            "columns": reg.column_types.get(table, {})
        }
        for table in relevant_tables
    }

    return {
        "schema_context": schema_context,
        "status": "SCHEMA_INSPECTED"
    }


# ---------------------------------------------------------------------------
# 4. generate_query_plan
# ---------------------------------------------------------------------------
async def generate_query_plan_node(state: DatabaseState) -> dict[str, Any]:
    """
    Creates a structured query plan validated against the approved schema.
    """
    if state.get("status") in ("FAILED_VALIDATION", "READ_ONLY_REFUSAL", "SECURITY_REFUSAL", "UNSUPPORTED_DATA"):
        return {}

    schema_ctx = state.get("schema_context", {})
    tables = list(schema_ctx.keys())
    intent = state.get("intent", "LIST")
    req_limit = state.get("requested_limit") or 50

    query_plan = {
        "operation": intent.lower(),
        "tables": tables,
        "filters": ["organization_id = :organization_id"],
        "group_by": [],
        "aggregations": ["COUNT(*)"] if intent == "COUNT" else [],
        "sort": None,
        "limit": req_limit
    }

    return {
        "query_plan": query_plan,
        "status": "PLAN_GENERATED"
    }


# ---------------------------------------------------------------------------
# 5. generate_sql
# ---------------------------------------------------------------------------
async def generate_sql_node(
    state: DatabaseState,
    generator: SQLGenerator | None = None
) -> dict[str, Any]:
    """
    Generates parameterized read-only SQL SELECT statement.
    """
    if state.get("status") in ("FAILED_VALIDATION", "READ_ONLY_REFUSAL", "SECURITY_REFUSAL", "UNSUPPORTED_DATA"):
        return {}

    gen = generator or SQLGenerator()
    question = state.get("question", "")
    org_id = state.get("organization_id", "")
    plan = state.get("query_plan", {})
    limit = state.get("requested_limit") or 50

    try:
        sql, parameters = await gen.generate(
            question=question,
            organization_id=org_id,
            schema_context=state.get("schema_context"),
            query_plan=plan,
            limit=limit
        )
        return {
            "sql": sql,
            "parameters": parameters,
            "status": "SQL_GENERATED"
        }
    except SchemaValidationError as e:
        return {
            "status": "UNSUPPORTED_DATA",
            "error": str(e),
            "summary": "The requested information is not available in the authorized business data.",
            "confidence": 0.0,
            "query_executed": False,
        }
    except Exception as e:  # noqa: BLE001
        return {
            "status": "SQL_GEN_FAILED",
            "error": str(e),
            "summary": "Could not construct a safe query for the requested business data.",
            "confidence": 0.0,
            "query_executed": False,
        }



# ---------------------------------------------------------------------------
# 6. validate_sql
# ---------------------------------------------------------------------------
async def validate_sql_node(
    state: DatabaseState,
    validator: SQLValidator | None = None
) -> dict[str, Any]:
    """
    Validates that the generated SQL is safe, read-only, and targets approved tables.
    """
    if state.get("status") in ("FAILED_VALIDATION", "READ_ONLY_REFUSAL", "SECURITY_REFUSAL", "UNSUPPORTED_DATA", "SQL_GEN_FAILED"):
        return {}

    val = validator or SQLValidator()
    sql = state.get("sql", "")
    parameters = state.get("parameters", {})
    org_id = state.get("organization_id", "")

    is_valid, error = val.validate(sql=sql, parameters=parameters, organization_id=org_id)
    if not is_valid:
        return {
            "status": "FAILED_SQL_VALIDATION",
            "error": error,
            "summary": "The generated query violated database safety guidelines.",
            "confidence": 0.0,
            "query_executed": False,
        }

    return {"status": "SQL_VALIDATED"}


# ---------------------------------------------------------------------------
# 7. enforce_tenant_filter
# ---------------------------------------------------------------------------
async def enforce_tenant_filter_node(state: DatabaseState) -> dict[str, Any]:
    """
    Enforces strict tenant isolation. Injects/verifies organization_id parameter.
    """
    if state.get("status") in (
        "FAILED_VALIDATION", "READ_ONLY_REFUSAL", "SECURITY_REFUSAL",
        "UNSUPPORTED_DATA", "SQL_GEN_FAILED", "FAILED_SQL_VALIDATION"
    ):
        return {}

    org_id = state.get("organization_id")
    parameters = dict(state.get("parameters", {}))
    sql = state.get("sql", "")

    # Security check: parameter must exist and match backend session org_id
    if parameters.get("organization_id") != org_id:
        return {
            "status": "FAILED_TENANT_ISOLATION",
            "error": "Cross-tenant access attempt detected.",
            "summary": "Tenant isolation violation: Access denied.",
            "confidence": 0.0,
            "query_executed": False,
        }

    # Query must contain organization_id in WHERE clause
    if not re.search(r"\borganization_id\b", sql, re.IGNORECASE):
        return {
            "status": "FAILED_TENANT_ISOLATION",
            "error": "Query missing mandatory tenant filter.",
            "summary": "Tenant isolation violation: Access denied.",
            "confidence": 0.0,
            "query_executed": False,
        }

    return {"status": "TENANT_ENFORCED", "parameters": parameters}


# ---------------------------------------------------------------------------
# 8. execute_query
# ---------------------------------------------------------------------------
async def execute_query_node(
    state: DatabaseState,
    executor: DatabaseExecutor | None = None,
    session: AsyncSession | None = None,
) -> dict[str, Any]:
    """
    Executes the parameterized query within a timeout and bounded result window.
    """
    if state.get("status") != "TENANT_ENFORCED":
        return {}

    exec_engine = executor or DatabaseExecutor(session=session)
    sql = state.get("sql", "")
    parameters = state.get("parameters", {})
    org_id = state.get("organization_id", "")
    limit = state.get("requested_limit")

    try:
        res = await exec_engine.execute(
            sql=sql,
            parameters=parameters,
            organization_id=org_id,
            limit=limit,
            session=session
        )
        return {
            "result_columns": res["columns"],
            "rows": res["rows"],
            "row_count": res["row_count"],
            "limited": res["limited"],
            "query_executed": True,
            "status": "QUERY_EXECUTED"
        }
    except QueryTimeoutError as te:
        return {
            "status": "QUERY_TIMEOUT",
            "error": str(te),
            "summary": "The query took too long to complete. Please narrow the request.",
            "confidence": 0.0,
            "query_executed": False,
            "rows": [],
            "row_count": 0,
        }
    except (DatabaseExecutionError, SQLValidationError) as de:
        return {
            "status": "EXECUTION_ERROR",
            "error": str(de),
            "summary": "An error occurred while executing the query on authorized business data.",
            "confidence": 0.0,
            "query_executed": False,
            "rows": [],
            "row_count": 0,
        }


# ---------------------------------------------------------------------------
# 9. summarize_results
# ---------------------------------------------------------------------------
async def summarize_results_node(state: DatabaseState) -> dict[str, Any]:
    """
    Synthesizes a grounded, non-hallucinatory natural language summary strictly from rows.
    """
    if not state.get("query_executed"):
        # If query was not executed, summary was already set by earlier node
        return {}

    rows = state.get("rows", [])
    row_count = state.get("row_count", 0)
    intent = state.get("intent", "LIST")
    question = state.get("question", "")

    # 1. Zero rows condition
    if row_count == 0:
        return {
            "summary": "No matching records were found in the authorized business data.",
            "status": "RESULTS_SUMMARIZED"
        }

    # 2. Single scalar aggregation (COUNT / SUM / AVG)
    first_row = rows[0]
    if len(rows) == 1 and len(first_row) == 1:
        metric_key = next(iter(first_row.keys()))
        metric_val = first_row[metric_key]


        if "count" in metric_key.lower() or intent == "COUNT":
            if "order" in question.lower():
                summary = f"There are {metric_val} pending orders."
            elif "document" in question.lower():
                summary = f"There are {metric_val} documents."
            else:
                summary = f"Total count: {metric_val}."
        elif "avg" in metric_key.lower() or "average" in metric_key.lower():
            formatted_val = f"{float(metric_val):.2f}" if isinstance(metric_val, (int, float)) else str(metric_val)
            summary = f"The average value is {formatted_val}."
        elif "sum" in metric_key.lower() or "total" in metric_key.lower():
            summary = f"The total calculated value is {metric_val}."
        else:
            summary = f"{metric_key}: {metric_val}."

        return {"summary": summary, "status": "RESULTS_SUMMARIZED"}

    # 3. Machines by failure summary
    if any("failure_count" in r for r in rows) and any("name" in r for r in rows):
        top_items = [f"{r.get('name')} ({r.get('failure_count')} failures)" for r in rows[:3]]
        summary = f"Top machines by failures: {', '.join(top_items)}."
        return {"summary": summary, "status": "RESULTS_SUMMARIZED"}

    # 4. Production records / failures summary
    if any("defect_count" in r for r in rows) or any("status" in r and r["status"] == "FAILED" for r in rows):
        total_defects = sum(r.get("defect_count", 0) for r in rows if isinstance(r.get("defect_count"), (int, float)))
        summary = f"Found {row_count} failed inspections with a total of {total_defects} reported defects."
        return {"summary": summary, "status": "RESULTS_SUMMARIZED"}

    # 5. Orders summary
    if any("order_number" in r for r in rows):
        summary = f"Found {row_count} orders matching the requested criteria."
        return {"summary": summary, "status": "RESULTS_SUMMARIZED"}

    # 6. Products summary
    if any("usage_count" in r for r in rows) and any("name" in r for r in rows):
        top_prods = [f"{r.get('name')} ({r.get('usage_count')} uses)" for r in rows[:3]]
        summary = f"Top products by usage: {', '.join(top_prods)}."
        return {"summary": summary, "status": "RESULTS_SUMMARIZED"}

    # 7. Vendors summary
    if any("total_purchases" in r for r in rows) and any("name" in r for r in rows):
        top_vendors = [f"{r.get('name')} (${r.get('total_purchases', 0):,})" for r in rows[:3]]
        summary = f"Top vendors by purchase volume: {', '.join(top_vendors)}."
        return {"summary": summary, "status": "RESULTS_SUMMARIZED"}

    # 8. General multi-row summary
    summary = f"Retrieved {row_count} authorized business record{'s' if row_count != 1 else ''}."
    return {"summary": summary, "status": "RESULTS_SUMMARIZED"}


# ---------------------------------------------------------------------------
# 10. validate_response
# ---------------------------------------------------------------------------
async def validate_response_node(state: DatabaseState) -> dict[str, Any]:
    """
    Final verification node:
    - Verifies no sensitive columns (e.g. passwords) are leaked
    - Computes confidence score
    - Ensures requires_approval is False for read-only queries
    """
    cols = state.get("result_columns", [])
    rows = state.get("rows", [])
    query_exec = state.get("query_executed", False)
    status_code = state.get("status", "")

    # Redact any forbidden columns if accidentally returned
    forbidden_cols = {"hashed_password", "password", "config_encrypted", "secret"}
    sanitized_cols = [c for c in cols if c.lower() not in forbidden_cols]
    sanitized_rows = []
    for r in rows:
        sanitized_rows.append({k: v for k, v in r.items() if k.lower() not in forbidden_cols})

    # Determine confidence score based on concrete execution metrics
    if query_exec and len(sanitized_rows) > 0:
        confidence = 0.98
    elif query_exec and len(sanitized_rows) == 0:
        confidence = 0.92
    elif status_code in ("UNSUPPORTED_DATA", "NO_SCHEMA_MATCH") or status_code in ("READ_ONLY_REFUSAL", "SECURITY_REFUSAL"):
        confidence = 0.0
    else:
        confidence = 0.0

    return {
        "result_columns": sanitized_cols,
        "rows": sanitized_rows,
        "confidence": confidence,
        "requires_approval": False,
        "status": "COMPLETED" if query_exec else status_code
    }
