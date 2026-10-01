import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    trigger_type = Column(String(50), nullable=False)
    trigger_config = Column(JSONB, default=dict, nullable=False)
    graph_definition = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    runs = relationship("WorkflowRun", back_populates="workflow", cascade="all, delete-orphan")

    @property
    def enabled(self) -> bool:
        return self.is_active

    @enabled.setter
    def enabled(self, val: bool) -> None:
        self.is_active = val

    @property
    def definition(self) -> dict:
        return self.graph_definition

    @definition.setter
    def definition(self, val: dict) -> None:
        self.graph_definition = val


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED
    current_step = Column(String(100), nullable=True, default="1")
    input_payload = Column(JSONB, default=dict, nullable=False)
    output_payload = Column(JSONB, nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error_details = Column(Text, nullable=True)

    workflow = relationship("Workflow", back_populates="runs")

    @property
    def context(self) -> dict:
        return self.input_payload

    @context.setter
    def context(self, val: dict) -> None:
        self.input_payload = val

    @property
    def completed_at(self) -> datetime | None:
        return self.finished_at

    @completed_at.setter
    def completed_at(self, val: datetime | None) -> None:
        self.finished_at = val

    @property
    def error(self) -> str | None:
        return self.error_details

    @error.setter
    def error(self, val: str | None) -> None:
        self.error_details = val

    @property
    def created_at(self) -> datetime:
        return self.started_at
