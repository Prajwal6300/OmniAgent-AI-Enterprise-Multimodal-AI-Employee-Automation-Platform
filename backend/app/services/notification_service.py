"""
OmniAgent AI — Notification Service
Handles tenant-isolated user notifications, unread counts, and status updates.
"""

from uuid import UUID, uuid4

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.schemas.notification import NotificationRead

logger = structlog.get_logger(__name__)


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_notifications(
        self,
        organization_id: UUID,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[NotificationRead]:
        stmt = (
            select(Notification)
            .where(
                Notification.organization_id == organization_id,
                Notification.user_id == user_id,
            )
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))

        res = await self.session.execute(stmt)
        return [NotificationRead.model_validate(n) for n in res.scalars().all()]

    async def get_unread_count(self, organization_id: UUID, user_id: UUID) -> int:
        stmt = (
            select(func.count(Notification.id))
            .where(
                Notification.organization_id == organization_id,
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar() or 0

    async def mark_as_read(
        self,
        notification_id: UUID,
        organization_id: UUID,
        user_id: UUID,
    ) -> bool:
        stmt = (
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.organization_id == organization_id,
                Notification.user_id == user_id,
            )
            .values(is_read=True)
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount > 0

    async def mark_all_as_read(self, organization_id: UUID, user_id: UUID) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.organization_id == organization_id,
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount

    async def create_notification(
        self,
        organization_id: UUID,
        user_id: UUID,
        title: str,
        message: str,
        notification_type: str = "INFO",
        link_url: str | None = None,
    ) -> Notification:
        notif = Notification(
            id=uuid4(),
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            link_url=link_url,
            is_read=False,
        )
        self.session.add(notif)
        await self.session.flush()
        return notif
