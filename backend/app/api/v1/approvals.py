from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.approval_service import ApprovalService
from app.schemas.approval import ApprovalDecision, ApprovalRead
from app.schemas.common import ResponseEnvelope

router = APIRouter(prefix="/approvals", tags=["Approvals"])

@router.post("/{approval_id}/decide", response_model=ResponseEnvelope[ApprovalRead])
async def decide_approval(
    approval_id: UUID,
    decision: ApprovalDecision,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    service = ApprovalService(session)
    res = await service.decide(approval_id, current_user.id, decision.decision, decision.reason)
    return ResponseEnvelope(data=res)
