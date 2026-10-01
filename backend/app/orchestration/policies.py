"""
OmniAgent AI — Orchestration Policies & Safe Transitions
Enforces deterministic transition rules, recursion protection, prompt injection defense,
and tenant boundary verification across multi-agent pipelines.
"""

import re
from typing import Any

from app.orchestration.errors import (
    PromptInjectionDetectedError,
    TenantSecurityViolationError,
    UnsafeTransitionError,
)
from app.orchestration.registry import normalize_agent_name

# Strictly authorized state transitions between cognitive agents
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "start": {
        "supervisor",
    },
    "supervisor": {
        "document_agent",
        "rag_agent",
        "database_agent",
        "vision_agent",
        "reasoning_agent",
        "action_agent",
        "finalize",
    },
    "reasoning_agent": {
        "document_agent",
        "rag_agent",
        "database_agent",
        "vision_agent",
        "action_agent",
        "finalize",
    },
    "document_agent": {
        "supervisor",
        "reasoning_agent",
        "finalize",
    },
    "rag_agent": {
        "supervisor",
        "reasoning_agent",
        "finalize",
    },
    "database_agent": {
        "supervisor",
        "reasoning_agent",
        "finalize",
    },
    "vision_agent": {
        "supervisor",
        "reasoning_agent",
        "finalize",
    },
    "action_agent": {
        "verify",
        "audit",
        "finalize",
    },
}

# Malicious prompt injection heuristics & patterns
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"system\s+prompt\s+override", re.IGNORECASE),
    re.compile(r"reveal\s+(all\s+)?(system\s+prompt|api\s+keys?|passwords?)", re.IGNORECASE),
    re.compile(r"exfiltrate\s+.*(to|via)\s+https?://", re.IGNORECASE),
    re.compile(r"send\s+(all\s+)?(company\s+data|records|database)\s+to\s+", re.IGNORECASE),
    re.compile(r"drop\s+database|delete\s+from\s+users|truncate\s+table", re.IGNORECASE),
]


class SafeTransitionPolicy:
    """Enforces legal agent-to-agent transitions to block recursion and arbitrary jumps."""

    @staticmethod
    def validate_transition(from_agent: str, to_agent: str) -> None:
        src = normalize_agent_name(from_agent)
        dst = normalize_agent_name(to_agent)

        # 1. Prohibit self-recursion
        if src == dst:
            raise UnsafeTransitionError(
                f"Recursive self-transition '{src}' -> '{dst}' is prohibited."
            )

        # 2. Check allowlist table
        allowed = ALLOWED_TRANSITIONS.get(src, set())
        if dst not in allowed and to_agent != "finalize" and to_agent != "end":
            raise UnsafeTransitionError(
                f"Unauthorized agent transition attempted: '{src}' -> '{dst}'. "
                f"Allowed transitions for '{src}': {sorted(allowed)}."
            )


class SecurityPolicy:
    """Enforces zero-trust input safety and strict multi-tenant boundaries."""

    @staticmethod
    def inspect_untrusted_text(content: str) -> None:
        """Inspects arbitrary text (user prompts, OCR, RAG chunks) for injection vectors."""
        if not content:
            return
        for pattern in PROMPT_INJECTION_PATTERNS:
            if pattern.search(content):
                raise PromptInjectionDetectedError(
                    "Security violation: Untrusted content matched forbidden prompt injection or exfiltration signature."
                )

    @staticmethod
    def enforce_tenant_context(organization_id: Any) -> str:
        """Validates that a non-empty authenticated organization_id is present."""
        if not organization_id or not str(organization_id).strip():
            raise TenantSecurityViolationError(
                "Access denied: Missing or invalid organization_id in security context."
            )
        return str(organization_id).strip()
