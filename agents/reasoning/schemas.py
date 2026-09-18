"""
OmniAgent AI — Reasoning Agent Schemas
Defines strongly typed Pydantic models for reasoning task classification,
execution plans, evidence models, conflict detection, and structured responses.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReasoningTaskType(str, Enum):
    """Supported Reasoning Task Classifications."""

    MULTI_SOURCE_ANALYSIS = "MULTI_SOURCE_ANALYSIS"
    COMPARISON = "COMPARISON"
    ROOT_CAUSE_ANALYSIS = "ROOT_CAUSE_ANALYSIS"
    TREND_ANALYSIS = "TREND_ANALYSIS"
    DECISION_SUPPORT = "DECISION_SUPPORT"
    CROSS_DOCUMENT_ANALYSIS = "CROSS_DOCUMENT_ANALYSIS"
    DOCUMENT_DATABASE_ANALYSIS = "DOCUMENT_DATABASE_ANALYSIS"
    IMAGE_DATABASE_ANALYSIS = "IMAGE_DATABASE_ANALYSIS"
    IMAGE_DOCUMENT_ANALYSIS = "IMAGE_DOCUMENT_ANALYSIS"
    GENERAL_REASONING = "GENERAL_REASONING"
    UNKNOWN = "UNKNOWN"


class EvidenceSourceType(str, Enum):
    """Source categories for normalized evidence items."""

    DOCUMENT = "DOCUMENT"
    RAG = "RAG"
    DATABASE = "DATABASE"
    IMAGE = "IMAGE"
    OCR = "OCR"
    OBJECT_DETECTION = "OBJECT_DETECTION"


class ConflictSeverity(str, Enum):
    """Severity ratings for factual discrepancies between sources."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Evidence(BaseModel):
    """
    Normalized factual evidence extracted from specialized agent outputs.
    Strictly grounded in verified downstream results; never fabricated.
    """

    model_config = ConfigDict(extra="ignore")

    source_type: str = Field(
        ...,
        description="Category: DOCUMENT, RAG, DATABASE, IMAGE, OCR, OBJECT_DETECTION",
    )
    source_id: str | None = Field(
        default=None, description="UUID or identifier of the source artifact"
    )
    source_name: str | None = Field(
        default=None,
        description="Human-readable filename, table name, or artifact name",
    )
    content: str = Field(
        ..., description="Factual extracted text, summary, or data observation"
    )
    page_number: int | None = Field(
        default=None, description="Document page number where applicable"
    )
    confidence: float | None = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary source metadata"
    )

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float | None) -> float | None:
        if v is None:
            return 1.0
        return max(0.0, min(1.0, round(v, 4)))


class EvidenceConflict(BaseModel):
    """
    Explicitly identified factual or state conflict between multiple sources.
    Prevents the agent from hallucinating an arbitrary resolution.
    """

    model_config = ConfigDict(extra="ignore")

    source_a: str = Field(
        ..., description="First evidence source, e.g. database_agent (machine_records)"
    )
    source_b: str = Field(
        ..., description="Second evidence source, e.g. vision_agent (inspection_image)"
    )
    claim_a: str = Field(..., description="Statement or metric asserted by source A")
    claim_b: str = Field(
        ..., description="Contradictory statement or metric asserted by source B"
    )
    severity: str = Field(
        default=ConflictSeverity.MEDIUM.value, description="Severity: LOW, MEDIUM, HIGH"
    )


class AgentExecutionStep(BaseModel):
    """Single discrete downstream agent invocation step."""

    model_config = ConfigDict(extra="ignore")

    agent_name: str = Field(..., description="Target specialized agent name")
    goal: str = Field(..., description="Objective or sub-query for this agent")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Injected invocation parameters"
    )


class ExecutionPlan(BaseModel):
    """Validated operational plan for required downstream specialist agents."""

    model_config = ConfigDict(extra="ignore")

    task_type: str = Field(default=ReasoningTaskType.GENERAL_REASONING.value)
    agents: list[str] = Field(
        default_factory=list, description="Allowlisted agent names to execute"
    )
    steps: list[AgentExecutionStep] = Field(
        default_factory=list, description="Ordered execution steps"
    )
    rationale: str = Field(
        default="", description="High-level reason for agent selection"
    )


class ReasoningAnalyzeRequest(BaseModel):
    """Public API request payload for Reasoning Agent analysis."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Complex analytical prompt or question",
    )
    conversation_id: str | None = Field(
        default=None, description="Optional UUID string of conversation context"
    )
    image_id: str | None = Field(
        default=None, description="Optional image UUID previously uploaded"
    )
    document_id: str | None = Field(
        default=None, description="Optional document UUID previously uploaded"
    )
    context: dict[str, Any] = Field(
        default_factory=dict, description="Optional conversational context parameters"
    )


# Backward-compatibility schema
class ReconciliationResult(BaseModel):
    """Legacy backward compatibility result schema."""

    is_matched: bool
    discrepancy_amount: float = 0.0
    risk_score: float = 0.0


class ReasoningResponse(BaseModel):
    """
    Comprehensive structured response produced by the Reasoning Agent.
    Strictly grounded in verified evidence without internal chain-of-thought exposure.
    """

    model_config = ConfigDict(extra="ignore")

    answer: str = Field(
        ..., description="Grounded, structured conclusion resolving the user's question"
    )
    task_type: str = Field(..., description="Classified reasoning task type")
    grounded: bool = Field(
        default=True,
        description="True if conclusion is strictly supported by verified evidence",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence reflecting evidence quality",
    )
    evidence: list[Evidence] = Field(
        default_factory=list, description="Normalized factual evidence considered"
    )
    conflicts: list[EvidenceConflict] = Field(
        default_factory=list, description="Detected discrepancies between sources"
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="Unresolved or missing data required for full certainty",
    )
    contributing_agents: list[str] = Field(
        default_factory=list,
        description="Agents whose outputs contributed to this analysis",
    )
    execution_plan: list[dict[str, Any]] = Field(
        default_factory=list, description="Downstream execution plan executed"
    )
    requires_approval: bool = Field(
        default=False,
        description="Whether action requires approval (always False for reasoning)",
    )
    latency_ms: float | None = Field(
        default=None, description="Total execution time in milliseconds"
    )
    reconciliation: ReconciliationResult | None = Field(
        default=None, description="Optional legacy reconciliation result"
    )

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, round(v, 4)))
