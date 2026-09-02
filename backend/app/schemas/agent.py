from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class AgentRunRequest(BaseModel):
    agent_name: str
    task_description: str
    conversation_id: Optional[UUID] = None
    context: Optional[Dict[str, Any]] = None

class ToolCallRead(BaseModel):
    id: UUID
    tool_name: str
    input_parameters: Dict[str, Any]
    output_result: Optional[Dict[str, Any]] = None
    risk_level: str
    status: str

class AgentRunRead(BaseModel):
    id: UUID
    agent_name: str
    task_description: str
    status: str
    latency_ms: Optional[int] = None
    total_tokens: int
    cost_usd: float
    started_at: datetime
    completed_at: Optional[datetime] = None
    tool_calls: List[ToolCallRead] = []

    class Config:
        from_attributes = True
