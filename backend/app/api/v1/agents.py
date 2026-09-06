from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.agent import (
    AgentRunRead,
    AgentRunRequest,
    SupervisorAnalyzeRequest,
    SupervisorDecision,
)
from app.schemas.common import ResponseEnvelope
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post("/run", response_model=ResponseEnvelope[AgentRunRead])
async def run_agent(
    request: AgentRunRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Executes a specialist agent run (legacy / direct run)."""
    service = AgentService(session)
    run = await service.run_agent(current_user.id, current_user.organization_id, request)
    return ResponseEnvelope(data=run)


@router.post("/supervisor/analyze", response_model=ResponseEnvelope[SupervisorDecision])
async def analyze_supervisor_request(
    request: SupervisorAnalyzeRequest,
    http_req: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Central cognitive routing analysis by Supervisor Agent.
    Classifies intent, selects target specialized agent, evaluates approval/tool requirements,
    and returns a structured operational task plan.
    """
    request_id = getattr(http_req.state, "request_id", None)
    service = AgentService(session)
    decision = await service.analyze_supervisor(
        user_id=current_user.id,
        org_id=current_user.organization_id,
        request=request,
        request_id=request_id
    )
    return ResponseEnvelope(data=decision)
