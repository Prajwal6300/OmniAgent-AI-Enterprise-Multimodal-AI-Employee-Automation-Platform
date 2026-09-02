from uuid import UUID
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workflow import Workflow, WorkflowRun

class WorkflowRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_org(self, org_id: UUID) -> List[Workflow]:
        stmt = select(Workflow).where(Workflow.organization_id == org_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, workflow: Workflow) -> Workflow:
        self.session.add(workflow)
        await self.session.flush()
        return workflow

    async def create_run(self, run: WorkflowRun) -> WorkflowRun:
        self.session.add(run)
        await self.session.flush()
        return run
