from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.agent_service import AgentService
from app.schemas.agent import AgentRunRequest, AgentRunRead
from app.schemas.common import ResponseEnvelope

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.post("/run", response_model=ResponseEnvelope[AgentRunRead])
async def run_agent(
    request: AgentRunRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    service = AgentService(session)
    run = await service.run_agent(current_user.id, current_user.organization_id, request)
    return ResponseEnvelope(data=run)
