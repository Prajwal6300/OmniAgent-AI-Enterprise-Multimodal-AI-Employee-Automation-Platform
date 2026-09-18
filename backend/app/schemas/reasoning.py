"""
OmniAgent AI — Reasoning Schemas for API Serialization
Defines request and response schemas for the Reasoning Agent API endpoints.
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReasoningEvidenceData(BaseModel):
    """Normalized evidence item serialized for API clients."""

    model_config = ConfigDict(from_attributes=True)

    source_type: str
    source_id: str | None = None
    source_name: str | None = None
    content: str
    page_number: int | None = None
    confidence: float | None = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReasoningConflictData(BaseModel):
    """Contradiction record between evidence sources."""

    model_config = ConfigDict(from_attributes=True)

    source_a: str
    source_b: str
    claim_a: str
    claim_b: str
    severity: str


class ReasoningAnalyzeRequest(BaseModel):
    """
    Payload for invoking Reasoning Agent analysis.
    User ID, Organization ID, and permissions are strictly injected via authentication middleware.
    """

    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        ..., min_length=1, max_length=5000, description="Natural language reasoning inquiry"
    )
    conversation_id: str | None = Field(
        default=None, description="Optional existing conversation UUID"
    )
    image_id: UUID | None = Field(
        default=None, description="Optional referenced image artifact UUID"
    )
    document_id: UUID | None = Field(
        default=None, description="Optional referenced document artifact UUID"
    )
    context: dict[str, Any] = Field(default_factory=dict, description="Optional context dictionary")


class ReasoningAnalyzeResponseData(BaseModel):
    """Structured response payload returned by POST /api/v1/agents/reasoning/analyze."""

    model_config = ConfigDict(from_attributes=True)

    answer: str
    task_type: str
    grounded: bool
    confidence: float
    evidence: list[ReasoningEvidenceData] = Field(default_factory=list)
    conflicts: list[ReasoningConflictData] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    contributing_agents: list[str] = Field(default_factory=list)
    execution_plan: list[dict[str, Any]] = Field(default_factory=list)
    requires_approval: bool = False
    latency_ms: float | None = None
