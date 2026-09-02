from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any
from pydantic import BaseModel

class ApprovalDecision(BaseModel):
    decision: str # APPROVED, REJECTED
    reason: Optional[str] = None

class ApprovalRead(BaseModel):
    id: UUID
    action_type: str
    risk_level: str
    action_payload: Dict[str, Any]
    reason: str
    status: str
    requested_by: Optional[UUID] = None
    decided_by: Optional[UUID] = None
    decision_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
