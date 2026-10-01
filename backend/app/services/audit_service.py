"""
OmniAgent AI — Cryptographic Audit Logging Service
Implements tamper-evident, SHA-256 prev_hash hash-chaining across audit and action audit logs,
with full tenant isolation and chain integrity verification.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import ActionAuditLog, _compute_action_audit_hash
from app.models.audit_log import AuditLog, _compute_audit_entry_hash

logger = structlog.get_logger(__name__)

GENESIS_HASH = "0" * 64


async def record_audit_log(
    session: AsyncSession,
    organization_id: UUID,
    user_id: UUID | None,
    event_type: str,
    resource_type: str,
    resource_id: str,
    details: dict[str, Any],
    ip_address: str | None = None,
) -> AuditLog:
    """
    Appends a new cryptographically chained audit log entry to the organization's chain.
    """
    stmt = (
        select(AuditLog)
        .where(AuditLog.organization_id == organization_id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(1)
    )
    res = await session.execute(stmt)
    latest = res.scalar_one_or_none()

    prev_hash = latest.entry_hash if latest else GENESIS_HASH
    entry_hash = _compute_audit_entry_hash(
        prev_hash=prev_hash,
        org_id=organization_id,
        user_id=user_id,
        event_type=event_type,
        resource_id=resource_id,
        details=details,
    )

    entry = AuditLog(
        id=uuid4(),
        organization_id=organization_id,
        user_id=user_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=str(resource_id),
        ip_address=ip_address,
        details=details,
        prev_hash=prev_hash,
        entry_hash=entry_hash,
        created_at=datetime.now(UTC),
    )
    session.add(entry)
    await session.flush()
    return entry


async def verify_audit_log_chain(
    session: AsyncSession,
    organization_id: UUID,
) -> tuple[bool, list[str]]:
    """
    Traverses the full audit log chain for an organization and validates cryptographic integrity.
    Returns (is_valid, list_of_violations).
    """
    stmt = (
        select(AuditLog)
        .where(AuditLog.organization_id == organization_id)
        .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
    )
    res = await session.execute(stmt)
    entries = list(res.scalars().all())

    if not entries:
        return True, []

    errors: list[str] = []
    expected_prev = GENESIS_HASH

    for i, entry in enumerate(entries):
        if entry.prev_hash != expected_prev:
            errors.append(
                f"Chain broken at entry index {i} (id={entry.id}): "
                f"expected prev_hash={expected_prev}, got {entry.prev_hash}"
            )

        computed = _compute_audit_entry_hash(
            prev_hash=entry.prev_hash,
            org_id=entry.organization_id,
            user_id=entry.user_id,
            event_type=entry.event_type,
            resource_id=entry.resource_id,
            details=entry.details,
        )
        if entry.entry_hash != computed:
            errors.append(
                f"Payload tampering detected at entry index {i} (id={entry.id}): "
                f"stored hash={entry.entry_hash}, computed hash={computed}"
            )

        expected_prev = entry.entry_hash

    return len(errors) == 0, errors


async def record_action_audit_log(
    session: AsyncSession,
    organization_id: UUID,
    user_id: UUID | None,
    action_id: str,
    action_type: str,
    event_type: str,
    status: str,
    risk_level: str,
    details: dict[str, Any],
    request_id: str | None = None,
    approval_id: str | None = None,
    external_reference: str | None = None,
) -> ActionAuditLog:
    """
    Appends a new cryptographically chained action audit log entry.
    """
    stmt = (
        select(ActionAuditLog)
        .where(ActionAuditLog.organization_id == organization_id)
        .order_by(ActionAuditLog.created_at.desc(), ActionAuditLog.id.desc())
        .limit(1)
    )
    res = await session.execute(stmt)
    latest = res.scalar_one_or_none()

    prev_hash = latest.entry_hash if latest else GENESIS_HASH
    entry_hash = _compute_action_audit_hash(
        prev_hash=prev_hash,
        organization_id=organization_id,
        user_id=user_id,
        event_type=event_type,
        resource_id=action_id,
        details=details,
    )

    entry = ActionAuditLog(
        id=uuid4(),
        organization_id=organization_id,
        user_id=user_id,
        action_id=str(action_id),
        action_type=action_type,
        event_type=event_type,
        status=status,
        risk_level=risk_level,
        request_id=request_id,
        approval_id=approval_id,
        external_reference=external_reference,
        details=details,
        prev_hash=prev_hash,
        entry_hash=entry_hash,
        created_at=datetime.now(UTC),
    )
    session.add(entry)
    await session.flush()
    return entry


async def verify_action_audit_log_chain(
    session: AsyncSession,
    organization_id: UUID,
) -> tuple[bool, list[str]]:
    """
    Traverses the full action audit log chain for an organization and validates integrity.
    """
    stmt = (
        select(ActionAuditLog)
        .where(ActionAuditLog.organization_id == organization_id)
        .order_by(ActionAuditLog.created_at.asc(), ActionAuditLog.id.asc())
    )
    res = await session.execute(stmt)
    entries = list(res.scalars().all())

    if not entries:
        return True, []

    errors: list[str] = []
    expected_prev = GENESIS_HASH

    for i, entry in enumerate(entries):
        if entry.prev_hash != expected_prev:
            errors.append(
                f"Action chain broken at index {i} (id={entry.id}): "
                f"expected prev_hash={expected_prev}, got {entry.prev_hash}"
            )

        computed = _compute_action_audit_hash(
            prev_hash=entry.prev_hash,
            organization_id=entry.organization_id,
            user_id=entry.user_id,
            event_type=entry.event_type,
            resource_id=entry.action_id,
            details=entry.details,
        )
        if entry.entry_hash != computed:
            errors.append(
                f"Action payload tampering detected at index {i} (id={entry.id}): "
                f"stored={entry.entry_hash}, computed={computed}"
            )

        expected_prev = entry.entry_hash

    return len(errors) == 0, errors