from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.models.user import User
from app.orchestration.state import UnifiedChatRequest, UnifiedChatResponse
from app.schemas.chat import MessageCreate, MessageRead
from app.schemas.common import ResponseEnvelope
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ResponseEnvelope[UnifiedChatResponse])
@router.post("/", response_model=ResponseEnvelope[UnifiedChatResponse], include_in_schema=False)
async def chat_endpoint(
    payload: UnifiedChatRequest,
    http_req: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Unified AI Chat Endpoint.
    Authenticates user, routes through Supervisor and specialized agents,
    gathers multi-source evidence, enforces human-in-the-loop approvals,
    and returns verified grounded responses.
    """
    request_id = getattr(http_req.state, "request_id", None)
    service = ChatService(session)
    response = await service.unified_chat(
        user_id=current_user.id,
        org_id=current_user.organization_id,
        payload=payload,
        request_id=request_id,
    )
    return ResponseEnvelope(data=response)


@router.post("/conversations/{conversation_id}/messages", response_model=ResponseEnvelope[MessageRead])
async def post_message(
    conversation_id: UUID,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Direct message persistence endpoint maintaining backward compatibility."""
    service = ChatService(session)
    msg = await service.send_message(current_user.id, current_user.organization_id, conversation_id, payload)
    return ResponseEnvelope(data=msg)
