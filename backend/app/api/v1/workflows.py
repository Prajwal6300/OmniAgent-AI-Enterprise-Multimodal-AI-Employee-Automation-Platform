from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.workflow_service import WorkflowService
from app.schemas.workflow import WorkflowRead
from app.schemas.common import ResponseEnvelope

router = APIRouter(prefix="/workflows", tags=["Workflows"])

@router.get("", response_model=ResponseEnvelope[List[WorkflowRead]])
async def list_workflows(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    service = WorkflowService(session)
    items = await service.list_workflows(current_user.organization_id)
    return ResponseEnvelope(data=items)
