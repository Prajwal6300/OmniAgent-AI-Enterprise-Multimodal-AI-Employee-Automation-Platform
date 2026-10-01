import hashlib
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AuditRepository(session)

    async def _get_last_hash(self, org_id: UUID) -> str:
        """Get the last entry_hash for the organization to chain from."""
        stmt = (
            select(AuditLog.entry_hash)
            .where(AuditLog.organization_id == org_id)
            .order_by(AuditLog.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return row[0] if row else "0" * 64

    async def record_event(
        self,
        org_id: UUID,
        user_id: UUID,
        event_type: str,
        resource_type: str,
        resource_id: str,
        details: dict,
        ip_address: str | None = None
    ) -> AuditLog:
        prev_hash = await self._get_last_hash(org_id)
        payload_str = json.dumps(details, sort_keys=True)
        raw = f"{prev_hash}:{org_id}:{user_id}:{event_type}:{resource_id}:{payload_str}"
        entry_hash = hashlib.sha256(raw.encode()).hexdigest()

        entry = AuditLog(
            organization_id=org_id,
            user_id=user_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            details=details,
            prev_hash=prev_hash,
            entry_hash=entry_hash
        )
        return await self.repo.log_entry(entry)

    async def list_by_org(self, org_id: UUID, limit: int = 100) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.organization_id == org_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())