"""
OmniAgent AI — Notifications API Endpoints
Provides tenant-isolated user notifications, unread counts, and mark-as-read actions.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.schemas.notification import NotificationRead, NotificationUnreadCount
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=ResponseEnvelope[list[NotificationRead]])
async def get_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = NotificationService(session)
    items = await service.list_notifications(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
    )
    return ResponseEnvelope(data=items)


@router.get("/unread-count", response_model=ResponseEnvelope[NotificationUnreadCount])
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = NotificationService(session)
    count = await service.get_unread_count(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )
    return ResponseEnvelope(data=NotificationUnreadCount(unread_count=count))


@router.post("/{notification_id}/read", response_model=ResponseEnvelope[dict])
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = NotificationService(session)
    success = await service.mark_as_read(
        notification_id=notification_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )
    return ResponseEnvelope(data={"success": success})


@router.post("/read-all", response_model=ResponseEnvelope[dict])
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = NotificationService(session)
    count = await service.mark_all_as_read(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )
    return ResponseEnvelope(data={"marked_read_count": count})
