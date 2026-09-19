"""
OmniAgent AI — Action Agent API Schemas
Defines request and response schemas for executing actions, managing human approvals,
and querying action history.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ActionExecuteRequest(BaseModel):
    """API payload for initiating an action execution."""
    model_config = ConfigDict(extra="forbid")

    action_type: str = Field(..., min_length=1, max_length=100, description="Type of action to execute")
    input: dict[str, Any] = Field(..., description="Action parameters dictionary")
    reason: str | None = Field(default="", max_length=1000, description="Optional business rationale")
    idempotency_key: str | None = Field(default=None, max_length=128, description="Optional client idempotency key")
    approval_id: str | None = Field(default=None, description="Optional UUID of pre-approved approval record")


class ActionExecuteResponse(BaseModel):
    """API response returned upon action execution or approval pause."""
    model_config = ConfigDict(extra="ignore")

    action_id: str
    action_type: str
    status: str
    success: bool
    message: str
    external_reference: str | None = None
    verified: bool = False
    requires_approval: bool = False
    approval_id: str | None = None
    data: dict[str, Any] | None = None
    execution_time_ms: float | None = None


class ActionApprovalRead(BaseModel):
    """API schema representing a human-in-the-loop approval record."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    action_id: UUID
    action_type: str
    organization_id: UUID
    requested_by: UUID | None = None
    payload_summary: str
    risk_level: str
    status: str
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime | None = None


class ActionApproveRequest(BaseModel):
    """Request payload for approving a pending action."""
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=1000, description="Optional approval comments")


class ActionRejectRequest(BaseModel):
    """Request payload for rejecting a pending action."""
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=1000, description="Reason for rejection")


class ActionHistoryItem(BaseModel):
    """Summary item for action audit history view."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    action_type: str
    risk_level: str
    status: str
    requested_by: UUID | None = None
    external_reference: str | None = None
    verified: bool
    created_at: datetime
    completed_at: datetime | None = None
