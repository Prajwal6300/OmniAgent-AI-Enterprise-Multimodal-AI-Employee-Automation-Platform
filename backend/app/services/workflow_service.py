"""
OmniAgent AI — Enterprise Workflow Application Service
Coordinates workflow CRUD, tenant boundaries, validation, execution runs, and audit.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.automation.engine.engine import WorkflowEngine
from app.automation.validator import WorkflowValidationError, validate_workflow_definition
from app.models.workflow import Workflow, WorkflowRun
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.workflow import WorkflowCreate, WorkflowRunCreate, WorkflowUpdate


class WorkflowService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = WorkflowRepository(session)
        self.engine = WorkflowEngine(session=session)

    async def create_workflow(self, org_id: UUID, user_id: UUID, payload: WorkflowCreate) -> Workflow:
        # 1. Validate definition
        defn = payload.graph_definition or {}
        if not defn and payload.trigger_type:
            defn = {"trigger": {"type": payload.trigger_type}, "steps": []}
        try:
            validated_defn = validate_workflow_definition(defn)
        except (WorkflowValidationError, ValueError, TypeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid workflow definition: {exc!s}",
            )

        now = datetime.now(UTC)
        workflow = Workflow(
            id=uuid4(),
            organization_id=org_id,
            created_by=user_id,
            name=payload.name,
            description=payload.description,
            trigger_type=payload.trigger_type,
            trigger_config=payload.trigger_config,
            graph_definition=validated_defn,
            is_active=payload.is_active,
            created_at=now,
            updated_at=now,
        )
        return await self.repo.create(workflow)

    async def list_workflows(self, org_id: UUID) -> list[Workflow]:
        return await self.repo.list_by_org(org_id)

    async def get_workflow(self, workflow_id: UUID, org_id: UUID) -> Workflow:
        wf = await self.repo.get(workflow_id, org_id)
        if not wf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow '{workflow_id}' not found.",
            )
        return wf

    async def update_workflow(self, workflow_id: UUID, org_id: UUID, payload: WorkflowUpdate) -> Workflow:
        wf = await self.get_workflow(workflow_id, org_id)
        if payload.name is not None:
            wf.name = payload.name
        if payload.description is not None:
            wf.description = payload.description
        if payload.trigger_type is not None:
            wf.trigger_type = payload.trigger_type
        if payload.trigger_config is not None:
            wf.trigger_config = payload.trigger_config
        if payload.graph_definition is not None:
            try:
                wf.graph_definition = validate_workflow_definition(payload.graph_definition)
            except (WorkflowValidationError, ValueError, TypeError) as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid workflow definition: {exc!s}",
                )
        if payload.is_active is not None:
            wf.is_active = payload.is_active
        wf.updated_at = datetime.now(UTC)
        return await self.repo.update(wf)

    async def delete_workflow(self, workflow_id: UUID, org_id: UUID) -> None:
        wf = await self.get_workflow(workflow_id, org_id)
        await self.repo.delete(wf)

    async def run_workflow(
        self,
        workflow_id: UUID,
        org_id: UUID,
        payload: WorkflowRunCreate | None = None,
    ) -> WorkflowRun:
        wf = await self.get_workflow(workflow_id, org_id)
        if not wf.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workflow '{wf.name}' is disabled and cannot be executed.",
            )

        run_id = uuid4()
        input_data = payload.input_payload if payload else {}

        # Create DB record
        run = WorkflowRun(
            id=run_id,
            workflow_id=workflow_id,
            organization_id=org_id,
            status="RUNNING",
            input_payload=input_data,
            current_step="1",
            started_at=datetime.now(UTC),
        )
        await self.repo.create_run(run)

        # Initialize engine run
        run_state = self.engine.init_run(
            run_id=str(run_id),
            workflow_id=str(workflow_id),
            organization_id=str(org_id),
            initial_data=input_data,
        )

        # Execute
        res_state = await self.engine.execute_workflow(wf.graph_definition, run_state)

        # Sync back to DB
        run.status = res_state.status
        run.current_step = str(res_state.current_step)
        run.output_payload = {
            "steps": [s.model_dump() for s in res_state.steps_history],
            "context": res_state.context,
        }
        run.error_details = res_state.error
        if res_state.status in ("COMPLETED", "FAILED", "CANCELLED"):
            run.finished_at = res_state.completed_at or datetime.now(UTC)

        await self.repo.update_run(run)
        return run

    async def list_runs(self, workflow_id: UUID, org_id: UUID) -> list[WorkflowRun]:
        await self.get_workflow(workflow_id, org_id)  # verify existence
        return await self.repo.list_runs_by_workflow(workflow_id, org_id)

    async def get_run(self, run_id: UUID, org_id: UUID) -> WorkflowRun:
        run = await self.repo.get_run(run_id, org_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow run '{run_id}' not found.",
            )
        return run

    async def cancel_run(self, run_id: UUID, org_id: UUID) -> WorkflowRun:
        run = await self.get_run(run_id, org_id)
        if run.status in ("COMPLETED", "FAILED", "CANCELLED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel run in status '{run.status}'.",
            )
        run.status = "CANCELLED"
        run.finished_at = datetime.now(UTC)
        run.error_details = "Cancelled by user request."
        await self.repo.update_run(run)
        return run

    async def resume_run(
        self,
        run_id: UUID,
        org_id: UUID,
        approval_id: str | None = None,
        decision: str = "APPROVED",
    ) -> WorkflowRun:
        run = await self.get_run(run_id, org_id)
        if run.status != "PAUSED":
            if run.status in ("COMPLETED", "APPROVED"):
                return run
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Run '{run_id}' is not in PAUSED status (current: {run.status}).",
            )
        wf = await self.get_workflow(run.workflow_id, org_id)
        res_state = await self.engine.resume_run(
            run_id=str(run_id),
            workflow_def=wf.graph_definition,
            approval_id=approval_id,
            decision=decision,
        )
        run.status = res_state.status
        run.current_step = str(res_state.current_step)
        run.output_payload = {
            "steps": [s.model_dump() for s in res_state.steps_history],
            "context": res_state.context,
        }
        run.error_details = res_state.error
        if res_state.status in ("COMPLETED", "FAILED", "CANCELLED"):
            run.finished_at = res_state.completed_at or datetime.now(UTC)
        await self.repo.update_run(run)
        return run
