"""
OmniAgent AI — SQL Generator
Generates safe, parameterized SELECT queries strictly against approved schemas.
Combines deterministic generation for common operational metrics with LLM fallback.
"""

import re
from typing import Any

from app.agents.database.exceptions import SchemaValidationError, UnsafeSQLError
from app.agents.database.schema_registry import SchemaRegistry, schema_registry


class SQLGenerator:
    """
    Generates safe, parameterized SQL SELECT statements strictly against approved schemas.
    """

    # Keywords that are strictly forbidden in generated queries
    FORBIDDEN_KEYWORDS = frozenset(
        {
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "ALTER",
            "TRUNCATE",
            "GRANT",
            "COPY",
            "CREATE",
        }
    )

    # Sort direction validation pattern
    SORT_DIRECTION_PATTERN = re.compile(r"^(ASC|DESC)$", re.IGNORECASE)

    def __init__(self, registry: SchemaRegistry | None = None):
        self.registry = registry or schema_registry

    def _validate_identifier(self, name: str, name_type: str, table: str | None = None) -> str:
        """
        Validate and safely pass an identifier (table or column).

        Raises SchemaValidationError if the identifier is not in the allowlist
        or does not match the expected pattern. Returns the validated name;
        safety comes from the allowlist plus the identifier regex, not from quoting.
        """
        IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
        if not IDENTIFIER_PATTERN.match(name):
            raise SchemaValidationError(
                f"Invalid {name_type} name '{name}': must match ^[A-Za-z_][A-Za-z0-9_]*$"
            )
        if name_type == "table" and not self.registry.is_table_allowed(name):
            raise SchemaValidationError(f"Table '{name}' is not in the authorized schema.")
        if name_type == "column" and table and not self.registry.is_column_allowed(table, name):
                raise SchemaValidationError(
                    f"Column '{name}' is not allowed for table '{table}'."
                )
        return name

    @classmethod
    def _check_forbidden_keywords(cls, sql: str) -> None:
        """
        Check that the SQL contains no forbidden DML/DDL keywords.
        Raises UnsafeSQLError if any are found.
        """
        upper = sql.upper()
        for keyword in cls.FORBIDDEN_KEYWORDS:
            # Check for keyword as a whole word, not as part of another word
            pattern = r"\b" + keyword + r"\b"
            if re.search(pattern, upper):
                raise UnsafeSQLError(
                    f"Forbidden SQL keyword detected: '{keyword}'"
                )

    @classmethod
    def _check_semicolons_and_comments(cls, sql: str) -> None:
        """
        Check that the SQL contains no semicolons or SQL comments.
        Raises UnsafeSQLError if found.
        """
        if ";" in sql:
            raise UnsafeSQLError("Semicolon detected in query: multiple statements not allowed")
        if "--" in sql:
            raise UnsafeSQLError("SQL comment '--' detected in query")
        if "/*" in sql or "*/" in sql:
            raise UnsafeSQLError("SQL block comment '/* */' detected in query")

    def _validate_sort_direction(self, sort_clause: str) -> str:
        """
        Validate that the sort direction is either ASC or DESC.
        Raises SchemaValidationError if invalid.
        """
        if not self.SORT_DIRECTION_PATTERN.match(sort_clause.upper()):
            raise SchemaValidationError(
                f"Invalid sort direction '{sort_clause}': must be ASC or DESC"
            )
        return sort_clause.upper()

    def _validate_limit(self, limit: int) -> int:
        """
        Validate and clamp the LIMIT value.
        Returns the clamped limit (max 500).
        """
        try:
            limit_int = int(limit)
        except (ValueError, TypeError):
            raise SchemaValidationError(f"Invalid LIMIT value: '{limit}' must be an integer")
        if limit_int < 1:
            raise SchemaValidationError("LIMIT must be a positive integer")
        return min(limit_int, 500)

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
                self._check_forbidden_keywords(sql)
                self._check_semicolons_and_comments(sql)
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
                self._check_forbidden_keywords(sql)
                self._check_semicolons_and_comments(sql)
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
            self._check_forbidden_keywords(sql)
            self._check_semicolons_and_comments(sql)
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
            self._check_forbidden_keywords(sql)
            self._check_semicolons_and_comments(sql)
            return sql, params

        # 4. Average production time
        if "production" in q and any(w in q for w in ["average", "avg", "mean"]) and ("time" in q or "duration" in q or "hours" in q):
            sql = (
                "SELECT AVG(production_time_hours) AS average_production_time_hours "
                "FROM production_records "
                "WHERE organization_id = :organization_id"
            )
            params = {"organization_id": organization_id}
            self._check_forbidden_keywords(sql)
            self._check_semicolons_and_comments(sql)
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
            self._check_forbidden_keywords(sql)
            self._check_semicolons_and_comments(sql)
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
            self._check_forbidden_keywords(sql)
            self._check_semicolons_and_comments(sql)
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
            self._check_forbidden_keywords(sql)
            self._check_semicolons_and_comments(sql)
            return sql, params

        # 8. Document counts / documents query
        if ("document" in q or "documents" in q) and any(w in q for w in ["how many", "count"]):
            sql = (
                "SELECT COUNT(*) AS total_documents "
                "FROM documents "
                "WHERE organization_id = :organization_id"
            )
            params = {"organization_id": organization_id}
            self._check_forbidden_keywords(sql)
            self._check_semicolons_and_comments(sql)
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

        # Validate table identifier
        safe_table = self._validate_identifier(table, "table")

        operation = query_plan.get("operation", "list").lower()
        limit = min(query_plan.get("limit", default_limit), 1000)
        params: dict[str, Any] = {"organization_id": organization_id}

        if operation == "count":
            query_parts = ["SELECT COUNT(*) AS total_count FROM", safe_table, "WHERE organization_id = :organization_id"]
            sql = " ".join(query_parts)
            self._check_forbidden_keywords(sql)
            self._check_semicolons_and_comments(sql)
            return sql, params

        elif operation == "aggregation":
            aggs = query_plan.get("aggregations", [])
            agg_expr = aggs[0] if aggs else "COUNT(*)"
            # Validate aggregate expression is a safe column expression
            if not self._is_safe_agg_expr(agg_expr):
                raise SchemaValidationError(f"Unsafe aggregate expression: '{agg_expr}'")
            # When a column is given (not *), require it to be in the allowlist for this table
            if agg_expr.upper().startswith(("AVG", "SUM", "MIN", "MAX")):
                col_name = agg_expr.strip().split("(", 1)[1].rstrip(")")
                if not self.registry.is_column_allowed(safe_table, col_name):
                    raise SchemaValidationError(
                        f"Column '{col_name}' is not allowed for table '{safe_table}'."
                    )
            query_parts = ["SELECT", agg_expr, "FROM", safe_table, "WHERE organization_id = :organization_id"]
            sql = " ".join(query_parts)
            self._check_forbidden_keywords(sql)
            self._check_semicolons_and_comments(sql)
            return sql, params

        else:
            cols = self.registry.column_allowlist.get(table, {"id"})
            # Exclude id and organization_id from top selected if other columns exist
            selected_cols = [c for c in cols if c not in ("organization_id")]
            # Validate each selected column
            safe_cols = []
            for c in selected_cols:
                self._validate_identifier(c, "column", table)
                safe_cols.append(c)
            col_str = ", ".join(safe_cols) if safe_cols else "*"

            # Validate and build sort clause
            sort_clause = ""
            if query_plan.get("sort"):
                sort_col = str(query_plan["sort"])
                # Validate sort column against allowlist for this table
                dir_match = re.search(r"\s+(ASC|DESC)$", sort_col, re.IGNORECASE)
                if dir_match:
                    sort_col_name = dir_match.group(0).strip().rstrip(" ASC").rstrip(" DESC").strip()
                    # Get the actual column name (everything before the direction)
                    sort_col_name = sort_col[:dir_match.start()].strip()
                    if sort_col_name not in self.registry.column_allowlist.get(table, set()):
                        raise SchemaValidationError(
                            f"Sort column '{sort_col_name}' is not allowed for table '{table}'."
                        )
                    validated_dir = self._validate_sort_direction(dir_match.group(1))
                    sort_clause = f" ORDER BY {sort_col_name} {validated_dir}"
                else:
                    # No direction specified, default to ASC after validation
                    sort_col_name = str(sort_col).strip()
                    if sort_col_name not in self.registry.column_allowlist.get(table, set()):
                        raise SchemaValidationError(
                            f"Sort column '{sort_col_name}' is not allowed for table '{table}'."
                        )
                    validated_dir = self._validate_sort_direction("ASC")
                    sort_clause = f" ORDER BY {sort_col_name} {validated_dir}"
            elif "created_at" in cols:
                sort_clause = " ORDER BY created_at DESC"

            parts = ["SELECT", col_str, "FROM", safe_table, "WHERE organization_id = :organization_id"]
            if sort_clause:
                parts.append(sort_clause.strip())
            parts.append("LIMIT :limit")
            sql = " ".join(parts)
            params["limit"] = limit
            self._check_forbidden_keywords(sql)
            self._check_semicolons_and_comments(sql)
            return sql, params

    AGG_EXPR_PATTERN = re.compile(
        r"^(COUNT|AVG|SUM|MIN|MAX)\((\*|[A-Za-z_][A-Za-z0-9_]*)\)$", re.IGNORECASE
    )

    def _is_safe_agg_expr(self, expr: str) -> bool:
        """
        Check that an aggregate expression is a known safe pattern.
        Only allows COUNT(*), COUNT(column), AVG(column), SUM(column), MIN(column), MAX(column).
        Column references must be in the column allowlist for the table.
        The * form is only allowed for COUNT.
        """
        normalized = expr.strip()
        match = self.AGG_EXPR_PATTERN.match(normalized)
        if not match:
            return False
        func = match.group(1).upper()
        col_or_asterisk = match.group(2)
        return func == "COUNT" and col_or_asterisk == "*" or func in ("AVG", "SUM", "MIN", "MAX") and col_or_asterisk != "*"

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
            if not self.registry.is_table_allowed(table):
                raise SchemaValidationError(f"Table '{table}' is not in the authorized schema.")
            safe_table = self._validate_identifier(table, "table")
            cols = self.registry.column_allowlist.get(table, {"id"})
            selected_cols = [c for c in cols if c != "organization_id"]
            # Validate each selected column
            safe_cols = []
            for c in selected_cols:
                self._validate_identifier(c, "column", table)
                safe_cols.append(c)
            col_str = ", ".join(safe_cols) if safe_cols else "*"
            query_parts = ["SELECT", col_str, "FROM", safe_table, "WHERE organization_id = :organization_id LIMIT :limit"]
            sql = " ".join(query_parts)
            params = {"organization_id": organization_id, "limit": limit}
            self._check_forbidden_keywords(sql)
            self._check_semicolons_and_comments(sql)
            return sql, params

        raise SchemaValidationError("The requested information is not available in the authorized business data.")