import uuid
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.agent_repository import AgentRepository
from app.models.agent_run import AgentRun
from app.schemas.agent import AgentRunRequest, SupervisorAnalyzeRequest, SupervisorDecision
from agents.supervisor import SupervisorAgent


class AgentService:
    def __init__(self, session: AsyncSession):
        self.agent_repo = AgentRepository(session)
        self._supervisor_agent = SupervisorAgent()

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

    async def analyze_supervisor(
        self,
        user_id: UUID,
        org_id: UUID,
        request: SupervisorAnalyzeRequest,
        request_id: Optional[str] = None
    ) -> SupervisorDecision:
        """
        Executes Supervisor Agent intent classification, capability mapping,
        and task plan generation using trusted tenant credentials.
        """
        decision = await self._supervisor_agent.analyze(
            message=request.message,
            conversation_id=request.conversation_id,
            user_id=str(user_id),
            organization_id=str(org_id),
            request_id=request_id,
            context=request.context
        )

        # Optional execution logging into AgentRun audit model
        try:
            conv_uuid = None
            if request.conversation_id:
                try:
                    conv_uuid = UUID(request.conversation_id)
                except (ValueError, TypeError):
                    conv_uuid = None

            run = AgentRun(
                organization_id=org_id,
                user_id=user_id,
                conversation_id=conv_uuid,
                agent_name="supervisor",
                task_description=request.message[:255],
                status="COMPLETED"
            )
            await self.agent_repo.create_run(run)
        except Exception:
            # Audit log persistence is non-blocking to prevent core routing degradation
            pass

        return decision
