"""
OmniAgent AI — Users API Endpoints
Provides profile lookup, tenant-scoped user listing, invitations, role updates, and deactivation.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.schemas.user import (
    AcceptInviteRequest,
    UserInviteRequest,
    UserInviteResponse,
    UserRead,
    UserRoleUpdateRequest,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=ResponseEnvelope[UserRead])
async def get_me(current_user: User = Depends(get_current_user)):
    return ResponseEnvelope(data=UserRead.model_validate(current_user))


@router.get("", response_model=ResponseEnvelope[list[UserRead]])
async def list_users(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = UserService(session)
    users = await service.list_users(current_user.organization_id)
    return ResponseEnvelope(data=users)


@router.post("/invite", response_model=ResponseEnvelope[UserInviteResponse])
async def invite_user(
    payload: UserInviteRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = UserService(session)
    try:
        res = await service.invite_user(current_user.organization_id, current_user, payload)
        return ResponseEnvelope(data=res, message="Invitation created successfully")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/accept-invite", response_model=ResponseEnvelope[UserRead], status_code=status.HTTP_201_CREATED)
async def accept_invite(
    payload: AcceptInviteRequest,
    session: AsyncSession = Depends(get_db_session),
):
    service = UserService(session)
    try:
        user = await service.accept_invite(payload)
        return ResponseEnvelope(data=user, message="Invitation accepted successfully")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{user_id}/role", response_model=ResponseEnvelope[UserRead])
async def update_user_role(
    user_id: UUID,
    payload: UserRoleUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = UserService(session)
    try:
        user = await service.update_user_role(user_id, current_user.organization_id, payload.role_id)
        return ResponseEnvelope(data=user, message="User role updated successfully")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/{user_id}", response_model=ResponseEnvelope[dict])
async def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = UserService(session)
    try:
        await service.deactivate_user(user_id, current_user.organization_id)
        return ResponseEnvelope(data={"deactivated": True}, message="User deactivated successfully")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
