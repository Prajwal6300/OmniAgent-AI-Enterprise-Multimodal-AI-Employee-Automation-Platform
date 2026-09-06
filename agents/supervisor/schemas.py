from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class TaskType(str, Enum):
    DOCUMENT_ANALYSIS = "DOCUMENT_ANALYSIS"
    IMAGE_ANALYSIS = "IMAGE_ANALYSIS"
    KNOWLEDGE_SEARCH = "KNOWLEDGE_SEARCH"
    DATABASE_QUERY = "DATABASE_QUERY"
    DATA_ANALYSIS = "DATA_ANALYSIS"
    REPORT_GENERATION = "REPORT_GENERATION"
    EMAIL = "EMAIL"
    WORKFLOW = "WORKFLOW"
    AUTOMATION = "AUTOMATION"
    GENERAL_QUERY = "GENERAL_QUERY"
    UNKNOWN = "UNKNOWN"


class AgentTarget(str, Enum):
    DOCUMENT_AGENT = "document_agent"
    VISION_AGENT = "vision_agent"
    RAG_AGENT = "rag_agent"
    DATABASE_AGENT = "database_agent"
    REASONING_AGENT = "reasoning_agent"
    ACTION_AGENT = "action_agent"
    SUPERVISOR = "supervisor"


PriorityLevel = Literal["low", "medium", "high"]


class SupervisorDecision(BaseModel):
    intent: str = Field(..., description="Identified specific user intent, e.g. invoice_comparison")
    task_type: str = Field(..., description="High-level category of the enterprise task")
    capability: str = Field(..., description="Required system capability")
    selected_agent: str = Field(..., description="Target specialized agent logical name")
    priority: PriorityLevel = Field(default="medium", description="Execution priority: low, medium, high")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    requires_tool: bool = Field(default=False, description="Whether the task will eventually require tool execution")
    requires_approval: bool = Field(default=False, description="Whether human-in-the-loop approval is required")
    task_plan: list[str] = Field(default_factory=list, description="Ordered operational task execution steps")
    explanation: str = Field(default="", description="Structured reasoning summary explaining the routing decision")
    
    # Backward-compatibility attributes for existing graph nodes and tests
    next_agent: str | None = Field(default=None, description="Legacy alias for selected_agent")
    reasoning: str | None = Field(default=None, description="Legacy alias for explanation")
    is_task_complete: bool = Field(default=False, description="Legacy flag for task completion")

    @model_validator(mode="after")
    def populate_compatibility_fields(self) -> "SupervisorDecision":
        if self.next_agent is None:
            # Map selected_agent to short name if needed, or keep exact agent name
            short_map = {
                "document_agent": "document",
                "vision_agent": "vision",
                "rag_agent": "rag",
                "database_agent": "database",
                "reasoning_agent": "reasoning",
                "action_agent": "action",
                "supervisor": "supervisor",
            }
            self.next_agent = short_map.get(self.selected_agent, self.selected_agent)
        if self.reasoning is None:
            self.reasoning = self.explanation
        return self

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError(f"Confidence score {v} must be between 0.0 and 1.0")
        return round(v, 4)


class SupervisorAnalyzeRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="User instruction or query to analyze")
    conversation_id: str | None = Field(default=None, description="Optional conversation UUID string")
    context: dict[str, Any] | None = Field(default_factory=dict, description="Optional conversational or tenant context")


class SupervisorAnalyzeData(BaseModel):
    intent: str
    task_type: str
    capability: str
    selected_agent: str
    priority: PriorityLevel
    confidence: float
    requires_tool: bool
    requires_approval: bool
    task_plan: list[str]
    explanation: str
    request_id: str | None = None
    latency_ms: float | None = None
