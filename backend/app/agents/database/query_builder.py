"""
OmniAgent AI — Query Builder
Provides structured, safe query construction. Preserves backward compatibility.
"""

from typing import Any


class QueryBuilder:
    """
    Constructs parameterized SELECT queries.
    Preserves backward compatibility with legacy build_select signature.
    """

    def build_select(self, table: str, columns: list[str], filters: dict[str, Any] | None = None) -> str:
        """
        Builds a basic SELECT string.
        """
        col_str = ", ".join(columns) if columns else "*"
        base_query = f"SELECT {col_str} FROM {table}"
        if filters:
            conditions = [f"{k} = :{k}" for k in filters]
            base_query += f" WHERE {' AND '.join(conditions)}"
        return base_query

