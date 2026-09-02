from uuid import UUID
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation, Message

class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_user(self, user_id: UUID) -> List[Conversation]:
        stmt = select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, conv_id: UUID) -> Optional[Conversation]:
        stmt = select(Conversation).where(Conversation.id == conv_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_conversation(self, conv: Conversation) -> Conversation:
        self.session.add(conv)
        await self.session.flush()
        return conv

    async def add_message(self, msg: Message) -> Message:
        self.session.add(msg)
        await self.session.flush()
        return msg
