from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.workflow_repository import WorkflowRepository

class WorkflowService:
    def __init__(self, session: AsyncSession):
        self.workflow_repo = WorkflowRepository(session)

    async def list_workflows(self, org_id: UUID):
        return await self.workflow_repo.list_by_org(org_id)
