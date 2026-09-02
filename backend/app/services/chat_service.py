from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.conversation_repository import ConversationRepository
from app.models.conversation import Conversation, Message
from app.schemas.chat import MessageCreate

class ChatService:
    def __init__(self, session: AsyncSession):
        self.conv_repo = ConversationRepository(session)

    async def send_message(self, user_id: UUID, org_id: UUID, conv_id: UUID, payload: MessageCreate):
        user_msg = Message(
            conversation_id=conv_id,
            sender_type="USER",
            content=payload.content
        )
        await self.conv_repo.add_message(user_msg)
        return user_msg
