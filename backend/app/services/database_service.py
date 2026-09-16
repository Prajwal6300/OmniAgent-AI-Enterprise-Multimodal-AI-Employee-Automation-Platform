"""
OmniAgent AI — Enterprise Database Service
Application service bridging FastAPI endpoints, multi-tenant authentication,
SQLAlchemy database sessions, audit logging, and the Database Agent.
"""

from uuid import UUID

from agents.database.agent import DatabaseAgent
from agents.database.schemas import DatabaseQueryRequest, DatabaseResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.agent_run import AgentRun
from app.repositories.agent_repository import AgentRepository


class DatabaseService:
    """
    Enterprise Application Service for the Database Agent.
    Enforces multi-tenant context injection, session lifecycle management,
    and non-blocking agent audit logging.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.agent_repo = AgentRepository(session)
        self.agent = DatabaseAgent(session=session)

    async def query(
        self,
        user_id: UUID,
        org_id: UUID,
        request: DatabaseQueryRequest,
        request_id: str | None = None,
        conversation_id: str | None = None,
    ) -> DatabaseResponse:
        """
        Executes tenant-isolated natural-language database query.
        """
        response = await self.agent.query(
            question=request.question,
            organization_id=str(org_id),
            user_id=str(user_id),
            limit=request.limit,
            request_id=request_id,
            conversation_id=conversation_id,
            session=self.session,
        )

        # Audit trace logging into AgentRun model
        try:
            run = AgentRun(
                organization_id=org_id,
                user_id=user_id,
                conversation_id=UUID(conversation_id) if conversation_id else None,
                agent_name="database_agent",
                task_description=request.question[:255],
                status="COMPLETED" if response.query_executed else "REFUSED",
            )
            await self.agent_repo.create_run(run)
        except Exception as audit_err:  # noqa: BLE001
            logger.warning("database_agent_audit_log_failed", error=str(audit_err))

        return response

