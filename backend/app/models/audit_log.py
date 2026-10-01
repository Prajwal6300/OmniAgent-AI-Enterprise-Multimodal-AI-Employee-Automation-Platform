import hashlib
import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


def _compute_audit_entry_hash(prev_hash: str, org_id, user_id, event_type: str, resource_id: str, details: dict) -> str:
    """Compute SHA-256 hash chaining from prev_hash + canonical payload."""
    payload_str = json.dumps(details, sort_keys=True)
    raw = f"{prev_hash}:{org_id}:{user_id}:{event_type}:{resource_id}:{payload_str}"
    return hashlib.sha256(raw.encode()).hexdigest()

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=True)
    details = Column(JSONB, nullable=False)
    prev_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
