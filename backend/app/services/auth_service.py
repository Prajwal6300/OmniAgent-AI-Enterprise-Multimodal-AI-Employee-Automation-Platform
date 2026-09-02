from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.core.exceptions import AuthenticationError
from app.schemas.auth import LoginRequest, Token

class AuthService:
    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)

    async def authenticate(self, request: LoginRequest) -> Token:
        user = await self.user_repo.get_by_email(request.email)
        if not user or not verify_password(request.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        return Token(access_token=access_token, refresh_token=refresh_token)
