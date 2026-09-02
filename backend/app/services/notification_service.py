from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification

class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def send_notification(self, org_id: UUID, user_id: UUID, title: str, message: str, n_type: str = "SYSTEM"):
        notification = Notification(
            organization_id=org_id,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=n_type
        )
        self.session.add(notification)
        await self.session.flush()
        return notification
