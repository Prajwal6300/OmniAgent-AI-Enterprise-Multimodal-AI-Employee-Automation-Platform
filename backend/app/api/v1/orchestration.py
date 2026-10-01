"""
OmniAgent AI — Orchestration API Endpoints
Provides direct operational access for running, resuming, cancelling, and inspecting orchestration workflows.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.models.user import User
from app.orchestration.errors import OrchestrationError
from app.orchestration.graph import Orchestrator
from app.orchestration.state import (
    ActionDetail,
    ApprovalDetail,
    CitationItem,
    EvidenceItem,
    ExecutionStepItem,
    ResumeRequest,
    UnifiedChatRequest,
    UnifiedChatResponse,
)
from app.schemas.common import ResponseEnvelope

router = APIRouter(prefix="/orchestration", tags=["Orchestration"])
orchestrator = Orchestrator()


def _build_unified_response(state: dict[str, Any]) -> UnifiedChatResponse:
    citations = [
        CitationItem(**c) if isinstance(c, dict) else c
        for c in state.get("citations", [])
    ]
    evidence = [
        EvidenceItem(**e) if isinstance(e, dict) else e
        for e in state.get("evidence", [])
    ]
    steps = [
        ExecutionStepItem(**s) if isinstance(s, dict) else s
        for s in state.get("execution_steps", [])
    ]

    action_obj = None
    act_res = state.get("action_result")
    if act_res:
        action_obj = ActionDetail(
            action_id=act_res.get("action_id", ""),
            action_type=act_res.get("action_type", ""),
            status=act_res.get("status", ""),
            success=act_res.get("success", False),
            verified=act_res.get("verified", False),
            external_reference=act_res.get("external_reference"),
            message=act_res.get("message"),
            data=act_res.get("data"),
        )

    approval_obj = None
    appr_det = state.get("approval_detail")
    if appr_det:
        approval_obj = ApprovalDetail(**appr_det)

    agents_used = [
        s.agent for s in steps if s.agent not in ("supervisor", "start")
    ]
    agents_used = sorted(set(agents_used))

    return UnifiedChatResponse(
        request_id=state.get("request_id", ""),
        conversation_id=state.get("conversation_id", ""),
        status=state.get("status", "COMPLETED"),
        answer=state.get("final_response") or "Analysis completed.",
        confidence=state.get("confidence", 1.0),
        grounded=state.get("grounded", True),
        citations=citations,
        evidence=evidence,
        agents_used=agents_used,
        execution_steps=steps,
        action=action_obj,
        approval=approval_obj,
        error=state.get("error"),
    )


@router.post("/run", response_model=ResponseEnvelope[UnifiedChatResponse])
async def run_orchestration(
    payload: UnifiedChatRequest,
    http_req: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Executes multi-agent orchestration directly."""
    req_id = getattr(http_req.state, "request_id", None)
    attachments_data = [a.model_dump() for a in payload.attachments]
    state = await orchestrator.execute(
        message=payload.message,
        organization_id=str(current_user.organization_id),
        user_id=str(current_user.id),
        conversation_id=str(payload.conversation_id) if payload.conversation_id else None,
        attachments=attachments_data,
        context=payload.context,
        session=session,
        request_id=req_id,
    )
    return ResponseEnvelope(data=_build_unified_response(state))


@router.post("/{request_id}/resume", response_model=ResponseEnvelope[UnifiedChatResponse])
async def resume_orchestration(
    request_id: str,
    payload: ResumeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Resumes a paused orchestration workflow after human review."""
    try:
        state = await orchestrator.resume(
            request_id=request_id,
            approval_id=payload.approval_id,
            organization_id=str(current_user.organization_id),
            user_id=str(current_user.id),
            decision=payload.decision,
            reason=payload.reason,
            session=session,
        )
        return ResponseEnvelope(data=_build_unified_response(state))
    except (OrchestrationError, ValueError, KeyError, RuntimeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{request_id}/cancel", response_model=ResponseEnvelope[UnifiedChatResponse])
async def cancel_orchestration(
    request_id: str,
    current_user: User = Depends(get_current_user),
):
    """Explicitly cancels an active or paused orchestration workflow."""
    try:
        state = await orchestrator.cancel(
            request_id=request_id,
            organization_id=str(current_user.organization_id),
        )
        return ResponseEnvelope(data=_build_unified_response(state))
    except (OrchestrationError, ValueError, KeyError, RuntimeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{request_id}/status", response_model=ResponseEnvelope[UnifiedChatResponse])
async def get_orchestration_status(
    request_id: str,
    current_user: User = Depends(get_current_user),
):
    """Fetches execution state for a workflow run."""
    state = orchestrator.get_state(request_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Request '{request_id}' not found.")
    if state.get("organization_id") != str(current_user.organization_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return ResponseEnvelope(data=_build_unified_response(state))


@router.get("/{request_id}/events", response_model=ResponseEnvelope[list[dict[str, Any]]])
async def get_orchestration_events(
    request_id: str,
    current_user: User = Depends(get_current_user),
):
    """Fetches execution events recorded during workflow execution."""
    from app.orchestration.events import event_recorder
    state = orchestrator.get_state(request_id)
    if not state or state.get("organization_id") != str(current_user.organization_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request events not found.")
    events = event_recorder.get_events(request_id)
    return ResponseEnvelope(data=[e.model_dump() for e in events])
