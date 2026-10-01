"""
OmniAgent AI — Unified Orchestration State
Defines the centralized TypedDict state model and Pydantic schemas for multi-agent workflows.
Enforces data minimization and prevents exposure of hidden chain-of-thought.
"""

from typing import Any, TypedDict

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    """Normalized evidence record from specialist agents."""
    source_type: str = Field(..., description="Source system: document, rag, database, vision, etc.")
    source_id: str = Field(default="", description="Identifier of the origin artifact")
    source_name: str = Field(default="", description="Human-readable title or table/document name")
    content: str = Field(..., description="Extracted factual excerpt or finding")
    page_number: int | None = Field(default=None, description="Page number if applicable")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CitationItem(BaseModel):
    """Citations verifying answer claims."""
    document_id: str = Field(default="")
    document_name: str = Field(default="")
    page_number: int | None = Field(default=None)
    section: str | None = Field(default=None)
    relevance_score: float | None = Field(default=None)


class ExecutionStepItem(BaseModel):
    """Step execution audit trail for UI observability."""
    agent: str
    action: str
    status: str  # STARTED, COMPLETED, FAILED, PAUSED
    timestamp: str
    duration_ms: float | None = None
    output_summary: str | None = None


class ApprovalDetail(BaseModel):
    """Structured approval information when execution pauses."""
    approval_id: str
    action_type: str
    risk_level: str = "MEDIUM"
    reason: str = ""
    payload_summary: str = ""
    input_payload: dict[str, Any] = Field(default_factory=dict)
    expires_at: str | None = None
    created_at: str | None = None


class ActionDetail(BaseModel):
    """Details of an executed action."""
    action_id: str
    action_type: str
    status: str
    success: bool
    verified: bool
    external_reference: str | None = None
    message: str | None = None
    data: dict[str, Any] | None = None


class OrchestrationState(TypedDict, total=False):
    """
    Unified LangGraph state schema spanning Supervisor, Specialists, Reasoning, and Action.
    Stores factual decisions, plans, evidence, and sanitized outputs.
    """
    request_id: str
    user_id: str
    organization_id: str
    conversation_id: str

    user_message: str
    attachments: list[dict[str, Any]]
    context: dict[str, Any]

    intent: str
    task_type: str
    priority: str

    current_agent: str
    previous_agent: str
    target_agent: str
    next_step: str

    execution_plan: list[dict[str, Any]]
    agent_outputs: dict[str, Any]

    evidence: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    conflicts: list[dict[str, Any]]
    artifacts: list[dict[str, Any]]

    pending_approval: bool
    approval_id: str | None
    approval_detail: dict[str, Any] | None

    action_requested: bool
    action_type: str | None
    action_input: dict[str, Any] | None
    action_result: dict[str, Any] | None

    execution_steps: list[dict[str, Any]]
    execution_events: list[dict[str, Any]]

    confidence: float
    grounded: bool

    status: str  # INITIALIZED, RUNNING, WAITING_FOR_APPROVAL, COMPLETED, PARTIAL_SUCCESS, FAILED, CANCELLED, TIMEOUT
    error: str | None
    final_response: str | None

    # Internal runtime execution fields
    start_time: float
    step_count: int
    agent_call_count: int
    retry_count: int
    is_cancelled: bool
    session: Any


# Pydantic Request & Response models for unified API

class AttachmentInput(BaseModel):
    type: str = Field(default="image", description="'image' | 'document' | 'file'")
    id: str | None = Field(default=None, description="Existing artifact ID if previously uploaded")
    filename: str | None = Field(default=None)
    mime_type: str | None = Field(default=None)
    content_b64: str | None = Field(default=None, description="Base64 encoded bytes for direct upload")
    url: str | None = Field(default=None)


class UnifiedChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="User instruction or prompt")
    conversation_id: str | None = Field(default=None, description="Optional conversation UUID")
    attachments: list[AttachmentInput] = Field(default_factory=list, description="Associated image/doc artifacts")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional enterprise context")


class UnifiedChatResponse(BaseModel):
    request_id: str
    conversation_id: str
    status: str = Field(..., description="COMPLETED | WAITING_FOR_APPROVAL | PARTIAL_SUCCESS | FAILED | CANCELLED")
    answer: str
    confidence: float = 1.0
    grounded: bool = True
    citations: list[CitationItem] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    agents_used: list[str] = Field(default_factory=list)
    execution_steps: list[ExecutionStepItem] = Field(default_factory=list)
    action: ActionDetail | None = None
    approval: ApprovalDetail | None = None
    error: str | None = None


class ResumeRequest(BaseModel):
    approval_id: str = Field(..., description="Approval UUID being confirmed")
    decision: str = Field(default="APPROVED", description="'APPROVED' or 'REJECTED'")
    reason: str | None = Field(default=None, description="Optional human rationale")
