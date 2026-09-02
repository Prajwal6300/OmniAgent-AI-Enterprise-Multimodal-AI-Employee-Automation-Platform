import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    agent_run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True)
    workflow_run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(100), nullable=False)
    risk_level = Column(String(20), nullable=False) # LOW, MEDIUM, HIGH
    action_payload = Column(JSONB, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False) # PENDING, APPROVED, REJECTED
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decided_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decision_reason = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    signature_hmac = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
