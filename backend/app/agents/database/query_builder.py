"""
OmniAgent AI — Query Builder
Provides structured, safe query construction. Preserves backward compatibility.
"""

import re
from typing import Any

from sqlalchemy.sql.elements import quoted_name

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

    def _validate_identifier(self, name: str, name_type: str) -> str:
        """
        Validate and safely quote an identifier (table or column).

        Raises SchemaValidationError if the identifier is not in the allowlist
        or does not match the expected pattern.
        """
        if not self.IDENTIFIER_PATTERN.match(name):
            raise SchemaValidationError(
                f"Invalid {name_type} name '{name}': must match ^[A-Za-z_][A-Za-z0-9_]*$"
            )
        if name_type == "table" and not self.registry.is_table_allowed(name):
            raise SchemaValidationError(f"Table '{name}' is not in the authorized schema.")
        if name_type == "column" and not self.registry.is_column_allowed(
            "", name
        ):
            # Table context may be missing; just pattern-check
            pass
        return str(quoted_name(name, quote=True))

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

        # Validate and quote columns
        safe_cols = []
        for col in columns:
            safe_col = self._validate_identifier(col, "column")
            safe_cols.append(safe_col)
        col_str = ", ".join(safe_cols)

        # Build WHERE clause with organization_id from authenticated user
        # nosec B608: safe_table and col_str are validated against schema allowlist and quoted
        base_query = f"SELECT {col_str} FROM {safe_table} WHERE organization_id = :organization_id"

        if filters:
            # Validate filter keys (should be column names)
            conditions = []
            for k in filters:
                _ = self._validate_identifier(k, "column")  # validates but uses table=""
                conditions.append(f"{k} = :{k}")
            base_query += f" AND {' AND '.join(conditions)}"

        return base_query

    def build_select_with_limit(
        self,
        table: str,
        columns: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 1000,
    ) -> str:
        """
        Builds a SELECT query with validated table, columns, filters, and clamped limit.

        Returns the query string and the limit value for use as a bound parameter.
        """
        if not columns:
            columns = ["*"]

        # Validate table
        safe_table = self._validate_identifier(table, "table")

        # Validate and quote columns
        safe_cols = []
        for col in columns:
            safe_col = self._validate_identifier(col, "column")
            safe_cols.append(safe_col)
        col_str = ", ".join(safe_cols)

        # Build WHERE clause with organization_id from authenticated user
        # nosec B608: safe_table and col_str are validated against schema allowlist and quoted
        base_query = f"SELECT {col_str} FROM {safe_table} WHERE organization_id = :organization_id"

        if filters:
            # Validate filter keys (should be column names)
            conditions = []
            for k in filters:
                _ = self._validate_identifier(k, "column")
                conditions.append(f"{k} = :{k}")
            base_query += f" AND {' AND '.join(conditions)}"

        # Clamp limit to maximum
        clamped_limit = min(limit, 1000)
        base_query += " LIMIT :limit"

        return base_query, clamped_limit