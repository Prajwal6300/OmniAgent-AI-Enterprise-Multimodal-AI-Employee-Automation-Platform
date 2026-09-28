"""
OmniAgent AI — Automation Workflow Run State
"""

from datetime import UTC, datetime
from typing import Any
from pydantic import BaseModel, Field


class StepRunResult(BaseModel):
    step_index: int
    step_type: str
    status: str  # COMPLETED, FAILED, SKIPPED, PAUSED
    name: str | None = None
    output: Any = None
    duration_ms: float | None = None
    error: str | None = None


class WorkflowRunState(BaseModel):
    run_id: str
    workflow_id: str
    organization_id: str = "default_org"
    status: str = "PENDING"  # PENDING, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED
    current_step: int = 0
    total_steps: int = 0
    context: dict[str, Any] = Field(default_factory=dict)
    steps_history: list[StepRunResult] = Field(default_factory=list)
    error: str | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
