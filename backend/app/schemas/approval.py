from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ApprovalDecision(BaseModel):
    decision: str # APPROVED, REJECTED
    reason: str | None = None

class ApprovalRead(BaseModel):
    id: UUID
    action_type: str
    risk_level: str
    action_payload: dict[str, Any]
    reason: str
    status: str
    requested_by: UUID | None = None
    decided_by: UUID | None = None
    decision_reason: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
