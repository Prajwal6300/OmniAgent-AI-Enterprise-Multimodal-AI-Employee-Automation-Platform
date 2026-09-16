"""
OmniAgent AI — SQL Generator
Generates parameterized, read-only SELECT queries with strict tenant isolation.
Combines deterministic generation for common operational metrics with LLM fallback.
"""

import re
from typing import Any

from agents.database.exceptions import SchemaValidationError
from agents.database.schema_registry import SchemaRegistry, schema_registry


class SQLGenerator:
    """
    Generates safe, parameterized SQL SELECT statements strictly against approved schemas.
    """

    def __init__(self, registry: SchemaRegistry | None = None):
        self.registry = registry or schema_registry

    def _generate_deterministic_query(
        self,
        question: str,
        organization_id: str,
        limit: int = 50
    ) -> tuple[str, dict[str, Any]] | None:
        """
        High-performance deterministic SQL generation for common enterprise business queries.
        Ensures 100% test reproducibility and zero-latency execution for known patterns.
        """
        q = question.strip().lower()

        # 1. Pending orders count
        if ("order" in q or "orders" in q) and any(w in q for w in ["pending", "open", "how many"]):
            if any(w in q for w in ["how many", "count"]):
                sql = (
                    "SELECT COUNT(*) AS pending_orders_count "
                    "FROM orders "
                    "WHERE organization_id = :organization_id AND status = :status"
                )
                params = {"organization_id": organization_id, "status": "PENDING"}
                return sql, params
            else:
                sql = (
                    "SELECT id, order_number, customer_name, status, total_amount, created_at "
                    "FROM orders "
                    "WHERE organization_id = :organization_id AND status = :status "
                    "ORDER BY created_at DESC "
                    "LIMIT :limit"
                )
                params = {"organization_id": organization_id, "status": "PENDING", "limit": limit}
                return sql, params

        # 2. Failed inspections / production failures
        if any(w in q for w in ["failed inspection", "failed inspections", "production failure", "production failures", "inspection failure", "inspection failures"]) or ("inspection" in q and "fail" in q):
            sql = (
                "SELECT id, batch_number, machine_id, defect_count, status, production_time_hours, created_at "
                "FROM production_records "
                "WHERE organization_id = :organization_id AND status = :status "
                "ORDER BY created_at DESC "
                "LIMIT :limit"
            )
            params = {"organization_id": organization_id, "status": "FAILED", "limit": limit}
            return sql, params

        # 3. Machines by failures (Top N machines)
        if ("machine" in q or "machines" in q) and any(w in q for w in ["failure", "failures", "fail", "failed"]):
            # Check for top N
            match_n = re.search(r"top\s+(\d+)", q)
            top_n = int(match_n.group(1)) if match_n else 5
            sql = (
                "SELECT id, name, machine_code, status, failure_count "
                "FROM machines "
                "WHERE organization_id = :organization_id "
                "ORDER BY failure_count DESC "
                "LIMIT :limit"
            )
            params = {"organization_id": organization_id, "limit": top_n}
            return sql, params

        # 4. Average production time
        if "production" in q and any(w in q for w in ["average", "avg", "mean"]) and ("time" in q or "duration" in q or "hours" in q):
            sql = (
                "SELECT AVG(production_time_hours) AS average_production_time_hours "
                "FROM production_records "
                "WHERE organization_id = :organization_id"
            )
            params = {"organization_id": organization_id}
            return sql, params

        # 5. Top products by usage
        if ("product" in q or "products" in q) and any(w in q for w in ["usage", "popular", "top"]):
            match_n = re.search(r"top\s+(\d+)", q)
            top_n = int(match_n.group(1)) if match_n else 10
            sql = (
                "SELECT id, name, sku, category, price, usage_count "
                "FROM products "
                "WHERE organization_id = :organization_id "
                "ORDER BY usage_count DESC "
                "LIMIT :limit"
            )
            params = {"organization_id": organization_id, "limit": top_n}
            return sql, params

        # 6. Purchase amount by vendor
        if ("vendor" in q or "vendors" in q or "supplier" in q) and any(w in q for w in ["purchase", "total", "amount", "spend"]):
            sql = (
                "SELECT id, name, total_purchases, rating "
                "FROM vendors "
                "WHERE organization_id = :organization_id "
                "ORDER BY total_purchases DESC "
                "LIMIT :limit"
            )
            params = {"organization_id": organization_id, "limit": limit}
            return sql, params

        # 7. Open maintenance requests
        if ("maintenance" in q or "repair" in q) and any(w in q for w in ["open", "pending", "request", "requests"]):
            sql = (
                "SELECT id, title, machine_id, status, priority, created_at "
                "FROM maintenance_requests "
                "WHERE organization_id = :organization_id AND status = :status "
                "ORDER BY created_at DESC "
                "LIMIT :limit"
            )
            params = {"organization_id": organization_id, "status": "OPEN", "limit": limit}
            return sql, params

        # 8. Document counts / documents query
        if ("document" in q or "documents" in q) and any(w in q for w in ["how many", "count"]):
            sql = (
                "SELECT COUNT(*) AS total_documents "
                "FROM documents "
                "WHERE organization_id = :organization_id"
            )
            params = {"organization_id": organization_id}
            return sql, params

        return None

    def _build_from_query_plan(
        self,
        query_plan: dict[str, Any],
        organization_id: str,
        default_limit: int = 50
    ) -> tuple[str, dict[str, Any]]:
        """
        Builds a safe parameterized SQL SELECT query dynamically from a validated query plan.
        """
        tables = query_plan.get("tables", [])
        if not tables:
            raise SchemaValidationError("Query plan does not specify any valid tables.")

        table = tables[0]
        if not self.registry.is_table_allowed(table):
            raise SchemaValidationError(f"Table '{table}' is not in the authorized schema.")

        operation = query_plan.get("operation", "list").lower()
        limit = min(query_plan.get("limit", default_limit), 500)
        params: dict[str, Any] = {"organization_id": organization_id}

        if operation == "count":
            sql = f"SELECT COUNT(*) AS total_count FROM {table} WHERE organization_id = :organization_id"
            return sql, params

        elif operation == "aggregation":
            aggs = query_plan.get("aggregations", [])
            agg_expr = aggs[0] if aggs else "COUNT(*)"
            sql = f"SELECT {agg_expr} FROM {table} WHERE organization_id = :organization_id"
            return sql, params

        else:
            cols = self.registry.column_allowlist.get(table, {"id"})
            # Exclude id and organization_id from top selected if other columns exist
            selected_cols = [c for c in cols if c not in ("organization_id")]
            col_str = ", ".join(sorted(selected_cols)) if selected_cols else "*"
            
            sort_clause = ""
            if query_plan.get("sort"):
                sort_clause = f" ORDER BY {query_plan['sort']}"
            elif "created_at" in cols:
                sort_clause = " ORDER BY created_at DESC"

            sql = f"SELECT {col_str} FROM {table} WHERE organization_id = :organization_id{sort_clause} LIMIT :limit"
            params["limit"] = limit
            return sql, params

    async def generate(
        self,
        question: str,
        organization_id: str,
        schema_context: dict[str, Any] | None = None,
        query_plan: dict[str, Any] | None = None,
        limit: int = 50
    ) -> tuple[str, dict[str, Any]]:
        """
        Generates a verified, read-only parameterized query and parameter dictionary.
        """
        # Step 1: Check deterministic generator
        deterministic = self._generate_deterministic_query(
            question=question,
            organization_id=organization_id,
            limit=limit
        )
        if deterministic is not None:
            return deterministic

        # Step 2: Build from Query Plan if available
        if query_plan and query_plan.get("tables"):
            return self._build_from_query_plan(
                query_plan=query_plan,
                organization_id=organization_id,
                default_limit=limit
            )

        # Step 3: Match relevant table and synthesize safe baseline query
        relevant = self.registry.identify_relevant_tables(question)
        if relevant:
            table = relevant[0]
            cols = self.registry.column_allowlist.get(table, {"id"})
            selected_cols = [c for c in cols if c != "organization_id"]
            col_str = ", ".join(sorted(selected_cols)) if selected_cols else "*"
            sql = f"SELECT {col_str} FROM {table} WHERE organization_id = :organization_id LIMIT :limit"
            params = {"organization_id": organization_id, "limit": limit}
            return sql, params

        raise SchemaValidationError("The requested information is not available in the authorized business data.")
