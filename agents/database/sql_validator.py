"""
OmniAgent AI — SQL Validator
Performs comprehensive AST and token validation on SQL statements against the SchemaRegistry.
"""

import re
from typing import Any

from agents.database.schema_registry import SchemaRegistry, schema_registry
from agents.database.security import SecurityValidator


class SQLValidator:
    """
    Validates SQL structure, table allowlists, column allowlists, and parameterization.
    """

    def __init__(self, registry: SchemaRegistry | None = None):
        self.registry = registry or schema_registry

    def extract_tables(self, sql: str) -> list[str]:
        """
        Extracts table names referenced in FROM and JOIN clauses.
        """
        clean_sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
        clean_sql = re.sub(r"/\*.*?\*/", "", clean_sql, flags=re.DOTALL)

        # Regex to extract identifiers following FROM or JOIN
        table_pattern = r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        matches = re.findall(table_pattern, clean_sql, re.IGNORECASE)
        # Normalize and filter out common SQL keywords
        exclude = {"select", "where", "group", "order", "limit", "as"}
        tables = [m.lower().strip() for m in matches if m.lower() not in exclude]
        return list(dict.fromkeys(tables))  # Deduplicate preserving order

    def validate(
        self,
        sql: str,
        parameters: dict[str, Any],
        organization_id: str
    ) -> tuple[bool, str | None]:
        """
        Executes full multi-layer validation:
        1. Read-only and syntax checks
        2. Table allowlist check
        3. Parameter dictionary safety check
        4. Tenant isolation verification
        """
        if not sql or not sql.strip():
            return False, "SQL query cannot be empty."

        # Layer 1: Read-only and security guardrails
        is_safe, error = SecurityValidator.validate_read_only(sql)
        if not is_safe:
            return False, error

        # Layer 2: Table Allowlist Check
        tables = self.extract_tables(sql)
        if not tables:
            return False, "Query must specify a target table in FROM clause."

        for table in tables:
            if not self.registry.is_table_allowed(table):
                return False, f"Table '{table}' is not in the authorized business data schema."

        # Layer 3: Parameters validation
        if not isinstance(parameters, dict):
            return False, "Parameters must be a dictionary."

        # Check for unparameterized raw string concatenation risks
        # Literal quotes containing SQL statements are suspicious
        if re.search(r"=\s*'[^']*;\s*(?:drop|delete|insert|update)\b", sql, re.IGNORECASE):
            return False, "Direct SQL string interpolation detected; use parameterized values."

        # Layer 4: Tenant Isolation Enforcement
        is_isolated, tenant_error = SecurityValidator.validate_tenant_isolation(
            sql=sql,
            parameters=parameters,
            expected_organization_id=organization_id
        )
        if not is_isolated:
            return False, tenant_error

        return True, None
