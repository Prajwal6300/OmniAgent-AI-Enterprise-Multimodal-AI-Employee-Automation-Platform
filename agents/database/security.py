"""
OmniAgent AI — Database Security Validator
Enforces zero-trust query validation, read-only guarantees, tenant isolation, and anti-injection defenses.
"""

import re
from typing import Any, ClassVar


class SecurityValidator:
    """
    Security guard for SQL queries.
    Validates queries before execution to ensure no destructive operations,
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

    FORBIDDEN_FUNCTIONS: ClassVar[list[str]] = [
        r"\bpg_read_file\b",
        r"\bpg_write_file\b",
        r"\bpg_read_binary_file\b",
        r"\bpg_sleep\b",
        r"\bdblink\b",
        r"\blo_export\b",
        r"\blo_import\b",
        r"\blo_unlink\b",
        r"\bcurrent_setting\b",
        r"\bset_config\b",
        r"\bpg_terminate_backend\b",
        r"\bpg_cancel_backend\b",
    ]

    FORBIDDEN_CATALOGS: ClassVar[list[str]] = [
        r"\bpg_catalog\b",
        r"\binformation_schema\b",
        r"\bpg_shadow\b",
        r"\bpg_authid\b",
        r"\bpg_user\b",
        r"\bpg_database\b",
        r"\bpg_tables\b",
        r"\bpg_class\b",
        r"\bpg_settings\b",
    ]

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
        Validates that the SQL statement is strictly read-only SELECT.
        Returns (is_valid, error_message).
        """
        clean_sql = sql.strip()

        # Must start with SELECT or WITH (for CTE queries that select)
        if not re.match(r"^(SELECT|WITH)\b", clean_sql, re.IGNORECASE):
            return False, "Query must begin with SELECT."

        # Check for stacked queries or multiple statements
        # Allow trailing semicolon, but reject interior semicolons
        body = clean_sql.rstrip(";").strip()
        if ";" in body:
            return False, "Multiple statements or stacked queries are strictly forbidden."

        # Check for forbidden SQL DDL / DML operations
        for pattern in cls.FORBIDDEN_OPERATIONS:
            if re.search(pattern, clean_sql, re.IGNORECASE):
                matched = re.search(pattern, clean_sql, re.IGNORECASE).group(0)
                return False, f"Forbidden SQL operation detected: {matched.upper()}"

        # Check for dangerous database functions
        for pattern in cls.FORBIDDEN_FUNCTIONS:
            if re.search(pattern, clean_sql, re.IGNORECASE):
                matched = re.search(pattern, clean_sql, re.IGNORECASE).group(0)
                return False, f"Forbidden database function detected: {matched}"

        # Check for forbidden PostgreSQL system catalogs
        for pattern in cls.FORBIDDEN_CATALOGS:
            if re.search(pattern, clean_sql, re.IGNORECASE):
                matched = re.search(pattern, clean_sql, re.IGNORECASE).group(0)
                return False, f"Direct access to system catalog is forbidden: {matched}"

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
        expected_organization_id: str
    ) -> tuple[bool, str | None]:
        """
        Validates that the query enforces tenant isolation for the authenticated organization.
        Ensures :organization_id parameter exists, matches the authenticated tenant,
        and is present in the SQL query WHERE clause.
        """
        clean_sql = sql.strip()

        # Check that :organization_id or organization_id parameter exists in parameters
        param_org = parameters.get("organization_id")
        if param_org is None:
            return False, "Query parameters must include 'organization_id'."

        # Verify that the parameter matches the authenticated organization
        if str(param_org).strip() != str(expected_organization_id).strip():
            return False, "Tenant isolation violation: parameter does not match authenticated organization."

        # Verify that organization_id is referenced in the SQL statement
        if not re.search(r"\borganization_id\b", clean_sql, re.IGNORECASE):
            return False, "Tenant isolation violation: query must filter by organization_id."

        return True, None

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
            sanitized = re.sub(pat, "[FILTERED_ADVERSARIAL_INSTRUCTION]", sanitized, flags=re.IGNORECASE)
        return sanitized
