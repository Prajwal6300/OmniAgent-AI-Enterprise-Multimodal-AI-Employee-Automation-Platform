from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


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

    class Config:
        from_attributes = True

