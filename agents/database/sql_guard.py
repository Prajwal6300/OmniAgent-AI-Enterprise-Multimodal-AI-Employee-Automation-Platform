import re

class SQLGuard:
    FORBIDDEN_PATTERNS = [
        r"\bDROP\b", r"\bDELETE\b", r"\bTRUNCATE\b",
        r"\bALTER\b", r"\bINSERT\b", r"\bUPDATE\b"
    ]

    def validate_read_only(self, sql: str) -> bool:
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                return False
        return True
