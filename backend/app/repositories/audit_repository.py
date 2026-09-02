from uuid import UUID
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog

class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_event(self, entry: AuditLog) -> AuditLog:
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list_by_org(self, org_id: UUID, limit: int = 100) -> List[AuditLog]:
        stmt = select(AuditLog).where(AuditLog.organization_id == org_id).order_by(AuditLog.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
