from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.workflow_service import WorkflowService
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowRead,
    WorkflowRunCreate,
    WorkflowRunRead,
    WorkflowUpdate,
)
from app.schemas.common import ResponseEnvelope

router = APIRouter(tags=["Workflows"])


@router.post("/workflows", response_model=ResponseEnvelope[WorkflowRead], status_code=status.HTTP_201_CREATED)
async def create_workflow(
    payload: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Creates a new enterprise workflow with validated definition."""
    service = WorkflowService(session)
    wf = await service.create_workflow(current_user.organization_id, current_user.id, payload)
    return ResponseEnvelope(data=WorkflowRead.model_validate(wf))


@router.get("/workflows", response_model=ResponseEnvelope[List[WorkflowRead]])
async def list_workflows(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Lists all workflows strictly within the authenticated organization."""
    service = WorkflowService(session)
    items = await service.list_workflows(current_user.organization_id)
    return ResponseEnvelope(data=[WorkflowRead.model_validate(w) for w in items])


@router.get("/workflows/{workflow_id}", response_model=ResponseEnvelope[WorkflowRead])
async def get_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieves a single workflow by ID within tenant boundaries."""
    service = WorkflowService(session)
    wf = await service.get_workflow(workflow_id, current_user.organization_id)
    return ResponseEnvelope(data=WorkflowRead.model_validate(wf))


@router.put("/workflows/{workflow_id}", response_model=ResponseEnvelope[WorkflowRead])
async def update_workflow(
    workflow_id: UUID,
    payload: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Updates an existing workflow with validated definitions."""
    service = WorkflowService(session)
    wf = await service.update_workflow(workflow_id, current_user.organization_id, payload)
    return ResponseEnvelope(data=WorkflowRead.model_validate(wf))


@router.delete("/workflows/{workflow_id}", response_model=ResponseEnvelope[dict])
async def delete_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Deletes a workflow and all associated runs under tenant isolation."""
    service = WorkflowService(session)
    await service.delete_workflow(workflow_id, current_user.organization_id)
    return ResponseEnvelope(data={"deleted": True, "workflow_id": str(workflow_id)})


@router.post("/workflows/{workflow_id}/run", response_model=ResponseEnvelope[WorkflowRunRead])
async def run_workflow(
    workflow_id: UUID,
    payload: WorkflowRunCreate = WorkflowRunCreate(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Triggers execution of a workflow run under tenant boundaries."""
    service = WorkflowService(session)
    run = await service.run_workflow(workflow_id, current_user.organization_id, payload)
    return ResponseEnvelope(data=WorkflowRunRead.model_validate(run))


@router.get("/workflows/{workflow_id}/runs", response_model=ResponseEnvelope[List[WorkflowRunRead]])
async def list_workflow_runs(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Lists execution runs for a specific workflow."""
    service = WorkflowService(session)
    runs = await service.list_runs(workflow_id, current_user.organization_id)
    return ResponseEnvelope(data=[WorkflowRunRead.model_validate(r) for r in runs])


@router.get("/workflow-runs/{run_id}", response_model=ResponseEnvelope[WorkflowRunRead])
async def get_workflow_run(
    run_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieves status and step execution details for a workflow run."""
    service = WorkflowService(session)
    run = await service.get_run(run_id, current_user.organization_id)
    return ResponseEnvelope(data=WorkflowRunRead.model_validate(run))


@router.post("/workflow-runs/{run_id}/cancel", response_model=ResponseEnvelope[WorkflowRunRead])
async def cancel_workflow_run(
    run_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Cancels an ongoing or paused workflow run."""
    service = WorkflowService(session)
    run = await service.cancel_run(run_id, current_user.organization_id)
    return ResponseEnvelope(data=WorkflowRunRead.model_validate(run))


@router.post("/workflow-runs/{run_id}/resume", response_model=ResponseEnvelope[WorkflowRunRead])
async def resume_workflow_run(
    run_id: UUID,
    payload: WorkflowRunCreate = WorkflowRunCreate(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Resumes a paused workflow run after human approval."""
    service = WorkflowService(session)
    appr_id = payload.input_payload.get("approval_id")
    decision = payload.input_payload.get("decision", "APPROVED")
    run = await service.resume_run(
        run_id=run_id,
        org_id=current_user.organization_id,
        approval_id=appr_id,
        decision=decision,
    )
    return ResponseEnvelope(data=WorkflowRunRead.model_validate(run))
