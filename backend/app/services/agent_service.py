from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.agent_repository import AgentRepository
from app.models.agent_run import AgentRun
from app.schemas.agent import AgentRunRequest

class AgentService:
    def __init__(self, session: AsyncSession):
        self.agent_repo = AgentRepository(session)

    async def run_agent(self, user_id: UUID, org_id: UUID, request: AgentRunRequest):
        run = AgentRun(
            organization_id=org_id,
            user_id=user_id,
            conversation_id=request.conversation_id,
            agent_name=request.agent_name,
            task_description=request.task_description,
            status="STARTED"
        )
        return await self.agent_repo.create_run(run)
