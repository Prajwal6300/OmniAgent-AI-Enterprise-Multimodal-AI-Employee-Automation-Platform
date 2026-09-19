import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


class ActionRecord(Base):
    __tablename__ = "actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(100), nullable=False, index=True)
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, PENDING_APPROVAL, APPROVED, REJECTED, RUNNING, COMPLETED, FAILED, VERIFICATION_FAILED, EXPIRED, CANCELLED
    idempotency_key = Column(String(128), nullable=True, index=True)
    input_hash = Column(String(64), nullable=True)
    input_payload = Column(JSONB, nullable=False)
    result_payload = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    external_reference = Column(String(255), nullable=True)
    verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class ActionApproval(Base):
    __tablename__ = "action_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    action_id = Column(UUID(as_uuid=True), ForeignKey("actions.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(100), nullable=False)
    payload_summary = Column(Text, nullable=False)
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, APPROVED, REJECTED, EXPIRED, CANCELLED
    payload_hash = Column(String(64), nullable=False)  # Cryptographic binding hash
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    decision_reason = Column(Text, nullable=True)
    signature_hmac = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class ActionAuditLog(Base):
    __tablename__ = "action_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_id = Column(String(100), nullable=False, index=True)
    action_type = Column(String(100), nullable=False)
    event_type = Column(String(100), nullable=False)  # ACTION_REQUESTED, ACTION_APPROVAL_REQUESTED, ACTION_APPROVED, ACTION_REJECTED, etc.
    status = Column(String(50), nullable=False)
    risk_level = Column(String(20), nullable=False)
    request_id = Column(String(100), nullable=True)
    approval_id = Column(String(100), nullable=True)
    external_reference = Column(String(255), nullable=True)
    details = Column(JSONB, nullable=False)
    entry_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
