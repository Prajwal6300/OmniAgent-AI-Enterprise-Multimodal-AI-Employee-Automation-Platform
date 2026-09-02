import hashlib
import json
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository

class AuditService:
    def __init__(self, session: AsyncSession):
        self.repo = AuditRepository(session)

    async def record_event(self, org_id: UUID, user_id: UUID, event_type: str, resource_type: str, resource_id: str, details: dict, ip_address: str = None):
        payload_str = json.dumps(details, sort_keys=True)
        raw = f"{org_id}:{user_id}:{event_type}:{resource_id}:{payload_str}"
        entry_hash = hashlib.sha256(raw.encode()).hexdigest()
        
        entry = AuditLog(
            organization_id=org_id,
            user_id=user_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            details=details,
            entry_hash=entry_hash
        )
        return await self.repo.log_event(entry)
