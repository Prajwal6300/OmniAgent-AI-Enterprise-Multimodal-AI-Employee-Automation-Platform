"""
OmniAgent AI — SQL Guard
Backward-compatible wrapper for security validation.
"""

from typing import ClassVar

from agents.database.security import SecurityValidator


class SQLGuard:
    """
    Validates that queries are strictly read-only and safe from injection attacks.
    Preserves backward compatibility with existing tests and modules.
    """

    FORBIDDEN_PATTERNS: ClassVar[list[str]] = [
        r"\bDROP\b", r"\bDELETE\b", r"\bTRUNCATE\b",
        r"\bALTER\b", r"\bINSERT\b", r"\bUPDATE\b",
        r"\bCREATE\b", r"\bGRANT\b", r"\bREVOKE\b"
    ]


    def validate_read_only(self, sql: str) -> bool:
        """
        Validates read-only status of a SQL query.
        Returns True if safe and read-only, False otherwise.
        """
        is_safe, _ = SecurityValidator.validate_read_only(sql)
        return is_safe
