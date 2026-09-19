"""
OmniAgent AI — Action Agent Approval Policy & Cryptographic Binding
Enforces backend-controlled approval requirements, cryptographic payload hashing,
binding validation, and expiration lifecycle management.
"""

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings

from agents.action.registry import action_registry
from agents.action.schemas import RiskLevel

# Risk policy mapping: actions requiring mandatory human authorization
DEFAULT_RISK_POLICY: dict[str, RiskLevel] = {
    "create_report": RiskLevel.LOW,
    "send_notification": RiskLevel.LOW,
    "send_email": RiskLevel.MEDIUM,
    "create_ticket": RiskLevel.MEDIUM,
    "erp_write": RiskLevel.HIGH,
    "financial_change": RiskLevel.HIGH,
    "delete_data": RiskLevel.CRITICAL,
}


def classify_action_risk(action_type: str) -> RiskLevel:
    """Classifies risk level for an action strictly based on backend policy."""
    act_lower = action_type.strip().lower()
    defn = action_registry.get(act_lower)
    if defn:
        return defn.risk_level
    return DEFAULT_RISK_POLICY.get(act_lower, RiskLevel.HIGH)


def requires_approval(action_type: str, risk_level: str | RiskLevel | None = None) -> bool:
    """
    Central deterministic approval policy.
    Evaluation is dictated entirely by backend logic, never by LLM output or user input.
    """
    act_lower = action_type.strip().lower()
    defn = action_registry.get(act_lower)
    if defn:
        return defn.approval_required

    r_level = RiskLevel(risk_level) if isinstance(risk_level, str) else (risk_level or classify_action_risk(act_lower))
    # Any MEDIUM, HIGH, or CRITICAL action not explicitly allowlisted without approval requires approval
    return r_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]


def compute_payload_hash(
    organization_id: str,
    user_id: str,
    action_type: str,
    normalized_input: dict[str, Any],
) -> str:
    """
    Generates a deterministic cryptographic SHA-256 hash binding an approval
    strictly to the tenant, requesting user, action type, and exact input parameters.
    """
    canonical_json = json.dumps(normalized_input, sort_keys=True, separators=(",", ":"))
    raw_binding = f"{organization_id}:{user_id}:{action_type.lower()}:{canonical_json}"
    return hashlib.sha256(raw_binding.encode("utf-8")).hexdigest()


def compute_approval_signature(approval_id: str, decision: str, decider_user_id: str) -> str:
    """Generates an HMAC-SHA256 signature validating decision authenticity."""
    secret = settings.SECRET_KEY.encode("utf-8")
    payload = f"{approval_id}:{decision}:{decider_user_id}".encode()
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()


def create_approval_expiry(minutes: int | None = None) -> datetime:
    """Calculates approval expiration timestamp."""
    exp_minutes = minutes if minutes is not None else settings.ACTION_APPROVAL_EXPIRATION_MINUTES
    return datetime.now(timezone.utc) + timedelta(minutes=exp_minutes)


def is_approval_expired(expires_at: datetime | None, now: datetime | None = None) -> bool:
    """Evaluates whether an approval token has exceeded its allowable lifetime."""
    if expires_at is None:
        return False
    current = now or datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return current > expires_at


def validate_approval_binding(
    stored_payload_hash: str,
    organization_id: str,
    user_id: str,
    action_type: str,
    normalized_input: dict[str, Any],
) -> bool:
    """
    Verifies that the approved action payload has not been modified or tampered with.
    """
    expected_hash = compute_payload_hash(
        organization_id=organization_id,
        user_id=user_id,
        action_type=action_type,
        normalized_input=normalized_input,
    )
    return hmac.compare_digest(stored_payload_hash, expected_hash)
