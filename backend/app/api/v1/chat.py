from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.chat_service import ChatService
from app.schemas.chat import MessageCreate, MessageRead
from app.schemas.common import ResponseEnvelope

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/conversations/{conversation_id}/messages", response_model=ResponseEnvelope[MessageRead])
async def post_message(
    conversation_id: UUID,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    service = ChatService(session)
    msg = await service.send_message(current_user.id, current_user.organization_id, conversation_id, payload)
    return ResponseEnvelope(data=msg)
