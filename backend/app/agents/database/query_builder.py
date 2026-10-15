"""
OmniAgent AI — Query Builder
Provides structured, safe query construction. Preserves backward compatibility.
"""

import re
from typing import Any

from app.agents.database.exceptions import SchemaValidationError
from app.agents.database.schema_registry import schema_registry


class QueryBuilder:
    """
    Constructs parameterized SELECT queries.
    Preserves backward compatibility with legacy build_select signature.
    """

    IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def __init__(self, registry: type[schema_registry] | None = None):
        self.registry = registry or schema_registry

    def _validate_identifier(self, name: str, name_type: str, table: str | None = None) -> str:
        """
        Validate and safely pass an identifier (table or column).

        Raises SchemaValidationError if the identifier is not in the allowlist
        or does not match the expected pattern. Returns the validated name;
        safety comes from the allowlist plus the identifier regex, not from quoting.
        """
        if not self.IDENTIFIER_PATTERN.match(name):
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

    def build_select(
        self,
        table: str,
        columns: list[str] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> str:
        """
        Builds a basic SELECT string with safety validations.

        Preserves backward compatibility with legacy build_select signature.
        """
        if not columns:
            columns = ["*"]

        # Validate table
        safe_table = self._validate_identifier(table, "table")

        # Handle "*" as the whole column list
        if columns == ["*"] or columns is None:
            col_str = "*"
        else:
            # Validate and pass columns
            safe_cols = []
            for col in columns:
                self._validate_identifier(col, "column", table)
                safe_cols.append(col)
            col_str = ", ".join(safe_cols)

        # Build WHERE clause with organization_id from authenticated user
        query_parts = ["SELECT", col_str, "FROM", safe_table, "WHERE organization_id = :organization_id"]
        base_query = " ".join(query_parts)

        if filters:
            # Validate filter keys (should be column names)
            conditions = []
            for k in filters:
                _ = self._validate_identifier(k, "column", table)  # validates with table context
                conditions.append(f"{k} = :{k}")
            base_query += f" AND {' AND '.join(conditions)}"

        return base_query

    def build_select_with_limit(
        self,
        table: str,
        columns: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 500,
    ) -> tuple[str, int]:
        """
        Builds a SELECT query with validated table, columns, filters, and clamped limit.

        Returns the query string and the limit value for use as a bound parameter.
        """
        if not columns:
            columns = ["*"]

        # Validate table
        safe_table = self._validate_identifier(table, "table")

        # Handle "*" as the whole column list
        if columns == ["*"] or columns is None:
            col_str = "*"
        else:
            # Validate and pass columns
            safe_cols = []
            for col in columns:
                self._validate_identifier(col, "column", table)
                safe_cols.append(col)
            col_str = ", ".join(safe_cols)

        # Build WHERE clause with organization_id from authenticated user
        query_parts = ["SELECT", col_str, "FROM", safe_table, "WHERE organization_id = :organization_id"]
        base_query = " ".join(query_parts)

        if filters:
            # Validate filter keys (should be column names)
            conditions = []
            for k in filters:
                _ = self._validate_identifier(k, "column", table)  # validates with table context
                conditions.append(f"{k} = :{k}")
            base_query += f" AND {' AND '.join(conditions)}"

        # Clamp limit to maximum (max 500)
        try:
            limit_int = int(limit)
        except (ValueError, TypeError):
            limit_int = 500
        limit_int = max(limit_int, 1)
        clamped_limit = min(limit_int, 500)
        base_query += " LIMIT :limit"

        return base_query, clamped_limit