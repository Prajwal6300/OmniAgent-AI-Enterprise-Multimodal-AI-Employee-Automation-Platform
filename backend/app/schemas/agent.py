from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AgentRunRequest(BaseModel):
    agent_name: str
    task_description: str
    conversation_id: UUID | None = None
    context: dict[str, Any] | None = None


class ToolCallRead(BaseModel):
    id: UUID
    tool_name: str
    input_parameters: dict[str, Any]
    output_result: dict[str, Any] | None = None
    risk_level: str
    status: str


class AgentRunRead(BaseModel):
    id: UUID
    agent_name: str
    task_description: str
    status: str
    latency_ms: int | None = None
    total_tokens: int
    cost_usd: float
    started_at: datetime
    completed_at: datetime | None = None
    tool_calls: list[ToolCallRead] = []

    model_config = ConfigDict(from_attributes=True)


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
