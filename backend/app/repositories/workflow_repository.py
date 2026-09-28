from typing import List, Optional
from uuid import UUID
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workflow import Workflow, WorkflowRun


class WorkflowRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_org(self, org_id: UUID) -> List[Workflow]:
        stmt = (
            select(Workflow)
            .where(Workflow.organization_id == org_id)
            .order_by(desc(Workflow.created_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, workflow_id: UUID, org_id: UUID) -> Optional[Workflow]:
        stmt = select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.organization_id == org_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, workflow: Workflow) -> Workflow:
        self.session.add(workflow)
        await self.session.flush()
        return workflow

    async def update(self, workflow: Workflow) -> Workflow:
        await self.session.flush()
        return workflow

    async def delete(self, workflow: Workflow) -> None:
        await self.session.delete(workflow)
        await self.session.flush()

    async def create_run(self, run: WorkflowRun) -> WorkflowRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def get_run(self, run_id: UUID, org_id: UUID) -> Optional[WorkflowRun]:
        stmt = select(WorkflowRun).where(
            WorkflowRun.id == run_id,
            WorkflowRun.organization_id == org_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_runs_by_workflow(self, workflow_id: UUID, org_id: UUID) -> List[WorkflowRun]:
        stmt = (
            select(WorkflowRun)
            .where(
                WorkflowRun.workflow_id == workflow_id,
                WorkflowRun.organization_id == org_id,
            )
            .order_by(desc(WorkflowRun.started_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_run(self, run: WorkflowRun) -> WorkflowRun:
        await self.session.flush()
        return run
