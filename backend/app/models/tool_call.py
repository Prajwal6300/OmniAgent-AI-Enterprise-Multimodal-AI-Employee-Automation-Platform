import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    agent_name = Column(String(100), nullable=False)
    task_description = Column(Text, nullable=False)
    status = Column(String(50), default="STARTED", nullable=False)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    total_tokens = Column(Integer, default=0, nullable=False)
    cost_usd = Column(Numeric(10, 6), default=0.0, nullable=False)
    error_message = Column(Text, nullable=True)

    tool_calls = relationship("ToolCall", back_populates="agent_run", cascade="all, delete-orphan")

class ToolCall(Base):
    __tablename__ = "tool_calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    agent_run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False)
    tool_name = Column(String(100), nullable=False)
    input_parameters = Column(JSONB, nullable=False)
    output_result = Column(JSONB, nullable=True)
    risk_level = Column(String(20), default="LOW", nullable=False)
    requires_approval = Column(Boolean, default=False, nullable=False)
    approval_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(50), default="PENDING", nullable=False)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    execution_latency_ms = Column(Integer, nullable=True)

    agent_run = relationship("AgentRun", back_populates="tool_calls")
