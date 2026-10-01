"""
OmniAgent AI — User Management Service
Handles tenant-scoped user listing, signed invitations, accept invite,
role updates, and deactivation with Last-Owner protection.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_invite_token,
    decode_invite_token,
    get_password_hash,
)
from app.models.role import Role
from app.models.user import User
from app.schemas.user import (
    AcceptInviteRequest,
    UserInviteRequest,
    UserInviteResponse,
    UserRead,
)

logger = structlog.get_logger(__name__)


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_users(self, organization_id: UUID) -> list[UserRead]:
        stmt = (
            select(User)
            .where(User.organization_id == organization_id)
            .order_by(User.created_at.asc())
        )
        res = await self.session.execute(stmt)
        return [UserRead.model_validate(u) for u in res.scalars().all()]

    async def invite_user(
        self,
        organization_id: UUID,
        current_user: User,
        req: UserInviteRequest,
    ) -> UserInviteResponse:
        email_clean = req.email.lower().strip()
        existing = await self.session.execute(
            select(User).where(User.email == email_clean)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"User with email {email_clean} already exists")

        # Verify role belongs to this org or is a system role
        role = await self.session.get(Role, req.role_id)
        if not role or (role.organization_id and role.organization_id != organization_id):
            raise ValueError("Invalid role specified for invitation")

        expires_delta = timedelta(days=7)
        token = create_invite_token(
            email=email_clean,
            organization_id=organization_id,
            role_id=req.role_id,
            expires_delta=expires_delta,
        )
        expires_at = datetime.now(UTC) + expires_delta

        return UserInviteResponse(
            invite_token=token,
            email=email_clean,
            expires_at=expires_at,
        )

    async def accept_invite(self, req: AcceptInviteRequest) -> UserRead:
        try:
            payload = decode_invite_token(req.invite_token)
        except Exception as exc:
            raise ValueError("Invalid or expired invitation token") from exc

        email = payload["email"].lower().strip()
        org_id = UUID(payload["org_id"])
        role_id = UUID(payload["role_id"])

        existing = await self.session.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise ValueError(f"User with email {email} is already registered")

        now = datetime.now(UTC)
        user = User(
            id=uuid4(),
            organization_id=org_id,
            email=email,
            full_name=req.full_name.strip(),
            hashed_password=get_password_hash(req.password),
            role_id=role_id,
            is_active=True,
            is_verified=True,
            created_at=now,
            updated_at=now,
        )
        self.session.add(user)
        await self.session.flush()
        return UserRead.model_validate(user)

    async def update_user_role(
        self,
        target_user_id: UUID,
        organization_id: UUID,
        new_role_id: UUID,
    ) -> UserRead:
        user = await self.session.get(User, target_user_id)
        if not user or user.organization_id != organization_id:
            raise ValueError("User not found in organization")

        # Check if new role is valid
        new_role = await self.session.get(Role, new_role_id)
        if not new_role:
            raise ValueError("Role not found")

        # Last Owner Protection: check if user is currently an owner being demoted
        current_role = await self.session.get(Role, user.role_id)
        is_current_owner = current_role and current_role.name.lower() in ("owner", "admin")
        is_new_owner = new_role.name.lower() in ("owner", "admin")

        if is_current_owner and not is_new_owner:
            owner_count = await self._count_active_owners(organization_id)
            if owner_count <= 1:
                raise ValueError("Demotion rejected: cannot demote the last remaining Owner of the organization")

        user.role_id = new_role_id
        user.updated_at = datetime.now(UTC)
        await self.session.flush()
        return UserRead.model_validate(user)

    async def deactivate_user(
        self,
        target_user_id: UUID,
        organization_id: UUID,
    ) -> None:
        user = await self.session.get(User, target_user_id)
        if not user or user.organization_id != organization_id:
            raise ValueError("User not found in organization")

        # Last Owner Protection: check if user is the last active Owner
        current_role = await self.session.get(Role, user.role_id)
        if current_role and current_role.name.lower() in ("owner", "admin"):
            owner_count = await self._count_active_owners(organization_id)
            if owner_count <= 1:
                raise ValueError("Deactivation rejected: cannot deactivate the last remaining Owner of the organization")

        user.is_active = False
        user.updated_at = datetime.now(UTC)
        await self.session.flush()

    async def _count_active_owners(self, organization_id: UUID) -> int:
        stmt = (
            select(func.count(User.id))
            .join(Role, User.role_id == Role.id)
            .where(
                User.organization_id == organization_id,
                User.is_active.is_(True),
                func.lower(Role.name).in_(["owner", "admin"]),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar() or 0
