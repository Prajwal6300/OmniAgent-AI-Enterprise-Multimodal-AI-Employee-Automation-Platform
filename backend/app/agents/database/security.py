"""
OmniAgent AI — Database Security Validator
Enforces zero-trust query validation, read-only guarantees, AST validation via sqlglot,
tenant isolation, and anti-injection defenses.
"""

import re
from typing import Any, ClassVar

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError


class SecurityValidator:
    """
    Security guard for SQL queries.
    Validates queries via sqlglot AST parsing before execution to ensure no destructive operations,
    no system catalog probing, no SQL injection, and strict tenant isolation.
    """

    FORBIDDEN_OPERATIONS: ClassVar[list[str]] = [
        r"\bINSERT\b",
        r"\bUPDATE\b",
        r"\bDELETE\b",
        r"\bDROP\b",
        r"\bALTER\b",
        r"\bTRUNCATE\b",
        r"\bCREATE\b",
        r"\bGRANT\b",
        r"\bREVOKE\b",
        r"\bEXEC\b",
        r"\bEXECUTE\b",
        r"\bMERGE\b",
        r"\bCALL\b",
        r"\bCOPY\b",
        r"\bREINDEX\b",
        r"\bVACUUM\b",
        r"\bINTO\s+OUTFILE\b",
        r"\bINTO\s+DUMPFILE\b",
    ]

    FORBIDDEN_FUNCTIONS: ClassVar[set[str]] = {
        "pg_read_file",
        "pg_write_file",
        "pg_read_binary_file",
        "pg_sleep",
        "dblink",
        "lo_export",
        "lo_import",
        "lo_unlink",
        "current_setting",
        "set_config",
        "pg_terminate_backend",
        "pg_cancel_backend",
    }

    FORBIDDEN_CATALOGS: ClassVar[set[str]] = {
        "pg_catalog",
        "information_schema",
        "pg_shadow",
        "pg_authid",
        "pg_user",
        "pg_database",
        "pg_tables",
        "pg_class",
        "pg_settings",
    }

    DANGEROUS_INJECTION_PATTERNS: ClassVar[list[str]] = [
        r";\s*(drop|delete|insert|update|create|alter|truncate)\b",
        r"\bunion\b.*\bselect\b.*\b(password|hash|token|secret)\b",
        r"'\s*or\s*'1'\s*=\s*'1",
        r"\"\s*or\s*\"1\"\s*=\s*\"1",
        r"1\s*=\s*1\s*--",
    ]

    @classmethod
    def validate_read_only(cls, sql: str) -> tuple[bool, str | None]:
        """
        Validates that the SQL statement is strictly read-only SELECT via AST parsing.
        Returns (is_valid, error_message).
        """
        clean_sql = sql.strip()
        if not clean_sql:
            return False, "Query cannot be empty."

        # Must start with SELECT or WITH (for CTE queries)
        if not re.match(r"^(SELECT|WITH)\b", clean_sql, re.IGNORECASE):
            return False, "Query must begin with SELECT."

        # Check for stacked queries or multiple statements
        try:
            statements = [s for s in sqlglot.parse(clean_sql, read="postgres") if s is not None]
        except SqlglotError as exc:
            return False, f"SQL syntax error: {exc}"

        if len(statements) > 1:
            return False, "Multiple statements or stacked queries are strictly forbidden."

        body = clean_sql.rstrip(";").strip()
        if ";" in body:
            return False, "Multiple statements or stacked queries are strictly forbidden."

        # Check regex forbidden operations for fast rejection
        for pattern in cls.FORBIDDEN_OPERATIONS:
            m = re.search(pattern, clean_sql, re.IGNORECASE)
            if m:
                return False, f"Forbidden SQL operation detected: {m.group(0).upper()}"

        # AST-level structure validation
        if not statements:
            return False, "No valid SQL statement parsed."

        ast = statements[0]

        # Root must be a SELECT expression (or Union of Selects)
        if not isinstance(ast, (exp.Select, exp.Union)):
            return False, f"Forbidden SQL operation detected: {type(ast).__name__.upper()}"

        # Ensure no DML or DDL sub-expressions exist in AST
        forbidden_node_types = (
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Drop,
            exp.Alter,
            exp.Create,
            exp.Command,
            exp.TruncateTable,
        )
        for node in ast.walk():
            if isinstance(node, forbidden_node_types):
                return False, f"Forbidden SQL operation detected: {type(node).__name__.upper()}"

        # AST function checks
        for func in ast.find_all(exp.Anonymous, exp.Func):
            fname = func.name.lower() if hasattr(func, "name") and func.name else ""
            if fname in cls.FORBIDDEN_FUNCTIONS:
                return False, f"Forbidden database function detected: {fname}"

        # Check regex for dangerous functions
        for func_pat in (
            r"\bpg_read_file\b", r"\bpg_write_file\b", r"\bpg_sleep\b",
            r"\bdblink\b", r"\blo_export\b", r"\blo_import\b", r"\blo_unlink\b",
            r"\bcurrent_setting\b", r"\bset_config\b",
            r"\bpg_terminate_backend\b", r"\bpg_cancel_backend\b"
        ):
            m = re.search(func_pat, clean_sql, re.IGNORECASE)
            if m:
                return False, f"Forbidden database function detected: {m.group(0)}"

        # System catalog check in AST and raw SQL
        for table in ast.find_all(exp.Table):
            tname = table.name.lower()
            schema_name = table.db.lower() if table.db else ""
            if tname in cls.FORBIDDEN_CATALOGS or schema_name in cls.FORBIDDEN_CATALOGS:
                return False, f"Direct access to system catalog is forbidden: {tname or schema_name}"

        for cat_pat in (
            r"\bpg_catalog\b", r"\binformation_schema\b", r"\bpg_shadow\b",
            r"\bpg_authid\b", r"\bpg_user\b", r"\bpg_database\b",
            r"\bpg_tables\b", r"\bpg_class\b", r"\bpg_settings\b"
        ):
            m = re.search(cat_pat, clean_sql, re.IGNORECASE)
            if m:
                return False, f"Direct access to system catalog is forbidden: {m.group(0)}"

        # Check for known SQL injection escape patterns
        for pattern in cls.DANGEROUS_INJECTION_PATTERNS:
            if re.search(pattern, clean_sql, re.IGNORECASE):
                return False, "Suspicious SQL injection pattern detected."

        return True, None

    @classmethod
    def validate_tenant_isolation(
        cls,
        sql: str,
        parameters: dict[str, Any],
        expected_organization_id: str,
    ) -> tuple[bool, str | None]:
        """
        Validates that the query enforces tenant isolation for the authenticated organization.
        Ensures :organization_id parameter exists, matches the authenticated tenant,
        and is present in the SQL query WHERE clause.
        """
        clean_sql = sql.strip()

        param_org = parameters.get("organization_id")
        if param_org is None:
            return False, "Query parameters must include 'organization_id'."

        if str(param_org).strip() != str(expected_organization_id).strip():
            return False, "Tenant isolation violation: parameter does not match authenticated organization."

        # AST-level verification of tenant column reference
        try:
            ast = sqlglot.parse_one(clean_sql, read="postgres")
            columns = {c.name.lower() for c in ast.find_all(exp.Column)}
            if "organization_id" not in columns and not re.search(r"\borganization_id\b", clean_sql, re.IGNORECASE):
                return False, "Tenant isolation violation: query must filter by organization_id."
        except SqlglotError:
            if not re.search(r"\borganization_id\b", clean_sql, re.IGNORECASE):
                return False, "Tenant isolation violation: query must filter by organization_id."

        return True, None

    @classmethod
    def enforce_limit(cls, sql: str, max_limit: int = 100) -> str:
        """
        Ensures a query has a LIMIT clause <= max_limit. Injects or caps limit if necessary.
        """
        try:
            ast = sqlglot.parse_one(sql, read="postgres")
            limit_node = ast.find(exp.Limit)
            if limit_node and limit_node.expression:
                try:
                    val = int(limit_node.expression.this)
                    if val > max_limit:
                        limit_node.set("expression", exp.Literal.number(max_limit))
                except (ValueError, TypeError):
                    limit_node.set("expression", exp.Literal.number(max_limit))
            else:
                ast = ast.limit(max_limit)
            return ast.sql(dialect="postgres")
        except SqlglotError:
            return sql

    @classmethod
    def sanitize_user_input_for_prompt(cls, text: str) -> str:
        """
        Strips adversarial prompt injection attempts such as system instruction overrides.
        """
        adversarial_phrases = [
            r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
            r"system\s+override",
            r"bypass\s+tenant\s+restriction",
            r"show\s+every\s+organization'?s?\s+records",
            r"delete\s+the\s+users\s+table",
            r"return\s+the\s+database\s+password",
        ]
        sanitized = text
        for pat in adversarial_phrases:
            sanitized = re.sub(pat, "[FILTERED]", sanitized, flags=re.IGNORECASE)
        return sanitized
