"""
OmniAgent AI — Action Agent Schemas
Defines strongly typed Pydantic models for action classification, input validation,
risk levels, execution results, approvals, and context.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ActionType(str, Enum):
    """Allowlisted executable action types."""
    SEND_EMAIL = "send_email"
    SEND_NOTIFICATION = "send_notification"
    CREATE_TICKET = "create_ticket"
    CREATE_REPORT = "create_report"


class RiskLevel(str, Enum):
    """Standardized operational risk classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActionStatus(str, Enum):
    """Explicit lifecycle execution statuses."""
    PENDING = "PENDING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ApprovalStatus(str, Enum):
    """Approval request status."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


# ==============================================================================
# Action Specific Input Schemas (Strict Validation & Data Minimization)
# ==============================================================================

class SendEmailInput(BaseModel):
    """Strict input schema for email dispatch."""
    model_config = ConfigDict(extra="forbid")

    recipient: EmailStr = Field(..., description="Target verified recipient email address")
    subject: str = Field(..., min_length=1, max_length=255, description="Subject line")
    body: str = Field(..., min_length=1, max_length=10000, description="Email body content")
    cc: list[EmailStr] | None = Field(default=None, description="Optional CC recipient email addresses")

    @field_validator("subject", "body")
    @classmethod
    def sanitize_header_injection(cls, v: str) -> str:
        # Prevent CRLF header injection in email subjects
        if "\n" in v or "\r" in v:
            return v.replace("\r", " ").replace("\n", " ").strip()
        return v.strip()


class SendNotificationInput(BaseModel):
    """Strict input schema for in-app or direct notification dispatch."""
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(..., min_length=1, max_length=128, description="Target recipient user ID")
    title: str = Field(..., min_length=1, max_length=255, description="Notification title")
    message: str = Field(..., min_length=1, max_length=5000, description="Notification message body")
    channel: Literal["IN_APP", "EMAIL"] = Field(default="IN_APP", description="Notification delivery channel")
    link_url: str | None = Field(default=None, max_length=500, description="Optional internal navigation link")


class CreateTicketInput(BaseModel):
    """Strict input schema for maintenance / incident ticket creation."""
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=255, description="Ticket title or issue summary")
    description: str = Field(..., min_length=1, max_length=5000, description="Detailed problem description")
    priority: Literal["LOW", "MEDIUM", "HIGH"] = Field(default="MEDIUM", description="Operational priority")
    machine_id: str | None = Field(default=None, max_length=128, description="Optional machine or asset identifier")


class CreateReportInput(BaseModel):
    """Strict input schema for internal report artifact generation."""
    model_config = ConfigDict(extra="forbid")

    report_type: str = Field(..., min_length=1, max_length=100, description="Category of report (e.g. INSPECTION)")
    title: str = Field(..., min_length=1, max_length=255, description="Report headline")
    summary: str = Field(..., min_length=1, max_length=10000, description="Executive narrative summary")
    data: dict[str, Any] | None = Field(default_factory=dict, description="Optional structured tabular data")


# ==============================================================================
# General Request, Proposal & Result Schemas
# ==============================================================================

class ActionProposal(BaseModel):
    """Backward compatibility action proposal schema."""
    model_config = ConfigDict(extra="ignore")

    tool_name: str
    parameters: dict[str, Any]
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    requires_approval: bool


class ActionRequest(BaseModel):
    """Structured request submitted to the Action Agent."""
    model_config = ConfigDict(extra="ignore")

    action_type: str = Field(..., description="Action type identifier, e.g. send_email")
    input: dict[str, Any] = Field(..., description="Action parameters dictionary")
    reason: str | None = Field(default="", description="Justification or business rationale")
    source_request_id: str | None = Field(default=None, description="Originating request or conversation UUID")
    idempotency_key: str | None = Field(default=None, max_length=128, description="Unique key for deduplication")
    approval_id: str | None = Field(default=None, description="Pre-approved approval record ID if already approved")


class ActionResult(BaseModel):
    """Standardized, safe result returned by the Action Agent."""
    model_config = ConfigDict(extra="ignore")

    action_id: str = Field(..., description="UUID of the executed action")
    action_type: str = Field(..., description="Executed action type")
    status: str = Field(..., description="Execution status enum")
    success: bool = Field(default=False, description="Whether execution succeeded")
    message: str = Field(..., description="Human-readable outcome message")
    external_reference: str | None = Field(default=None, description="External provider reference, message ID, or artifact path")
    verified: bool = Field(default=False, description="Whether side-effect verification succeeded")
    requires_approval: bool = Field(default=False, description="Whether execution paused for human approval")
    approval_id: str | None = Field(default=None, description="Approval ID if approval is pending or applied")
    data: dict[str, Any] | None = Field(default=None, description="Safe result data")
    execution_time_ms: float | None = Field(default=None, description="Execution duration in milliseconds")


class ActionContext(BaseModel):
    """Authenticated tenant and user security context."""
    model_config = ConfigDict(extra="ignore")

    user_id: str = Field(..., description="Authenticated user UUID")
    organization_id: str = Field(..., description="Authenticated organization UUID")
    user_role: str = Field(default="Operator", description="User role name, e.g. Admin, Supervisor")
    user_permissions: list[str] = Field(default_factory=list, description="Explicit granted permission codes")
    request_id: str | None = Field(default=None, description="Unique request tracing ID")
    conversation_id: str | None = Field(default=None, description="Conversation session ID")
    ip_address: str | None = Field(default=None, description="Origin IP address")


class ActionApprovalRead(BaseModel):
    """Public read model for human-in-the-loop approvals."""
    model_config = ConfigDict(extra="ignore")

    approval_id: str
    action_id: str
    action_type: str
    organization_id: str
    requested_by: str | None = None
    payload_summary: str
    risk_level: str
    status: str
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    expires_at: datetime
    created_at: datetime
