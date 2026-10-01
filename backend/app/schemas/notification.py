"""
OmniAgent AI — Notification Schemas
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    user_id: UUID
    title: str
    message: str
    notification_type: str
    is_read: bool
    link_url: str | None = None
    created_at: datetime | None = None


class NotificationUnreadCount(BaseModel):
    unread_count: int
