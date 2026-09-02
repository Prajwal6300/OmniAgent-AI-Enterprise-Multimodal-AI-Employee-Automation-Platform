from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user import UserCreate

class UserService:
    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)

    async def get_user_by_id(self, user_id: UUID):
        return await self.user_repo.get_by_id(user_id)
