"""
OmniAgent AI — Authentication Service
Handles login, bootstrap registration, refresh token rotation with Redis revocation, and logout.
"""

import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.redis import is_token_revoked, revoke_token
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.role import Role
from app.models.user import Organization, User
from app.schemas.auth import LoginRequest, RegisterRequest, Token

logger = structlog.get_logger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def authenticate(self, request: LoginRequest) -> Token:
        stmt = select(User).where(User.email == request.email.lower().strip())
        res = await self.session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user or not verify_password(request.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        return Token(access_token=access_token, refresh_token=refresh_token)

    async def register(self, request: RegisterRequest) -> Token:
        """
        Bootstrap registration: creates a new organization and provisions the first user as Owner.
        """
        normalized_email = request.email.lower().strip()
        existing = await self.session.execute(select(User).where(User.email == normalized_email))
        if existing.scalar_one_or_none():
            raise AuthenticationError("A user with this email address already exists")

        # Generate slug from organization name
        base_slug = re.sub(r"[^a-z0-9]+", "-", request.organization_name.lower()).strip("-") or "org"
        slug = f"{base_slug}-{uuid4().hex[:6]}"

        now = datetime.now(UTC)
        org = Organization(
            id=uuid4(),
            name=request.organization_name.strip(),
            slug=slug,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self.session.add(org)
        await self.session.flush()

        # Provision Owner role for organization
        owner_role = Role(
            id=uuid4(),
            organization_id=org.id,
            name="Owner",
            description="Organization owner with unrestricted administrative privileges",
            is_system_role=True,
            created_at=now,
        )
        self.session.add(owner_role)
        await self.session.flush()

        # Create user as verified Owner
        user = User(
            id=uuid4(),
            organization_id=org.id,
            email=normalized_email,
            hashed_password=get_password_hash(request.password),
            full_name=request.full_name.strip(),
            role_id=owner_role.id,
            is_active=True,
            is_verified=True,
            created_at=now,
            updated_at=now,
        )
        self.session.add(user)
        await self.session.flush()

        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        return Token(access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, refresh_token: str) -> Token:
        """
        Refreshes access token with strict single-use token rotation and Redis revocation checks.
        """
        if await is_token_revoked(refresh_token):
            raise AuthenticationError("Refresh token has been revoked")

        try:
            payload = decode_token(refresh_token)
        except Exception as exc:
            raise AuthenticationError("Invalid or expired refresh token") from exc

        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type: expected refresh token")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationError("Invalid token payload")

        user = await self.session.get(User, UUID(user_id_str))
        if not user or not user.is_active:
            raise AuthenticationError("User account not found or disabled")

        # Invalidate old refresh token (rotation enforcement)
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await revoke_token(refresh_token, expires_in_seconds=ttl)

        # Issue new token pair
        new_access = create_access_token(subject=str(user.id))
        new_refresh = create_refresh_token(subject=str(user.id))
        return Token(access_token=new_access, refresh_token=new_refresh)

    async def logout(self, refresh_token: str) -> None:
        """Revokes the refresh token in Redis."""
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await revoke_token(refresh_token, expires_in_seconds=ttl)
