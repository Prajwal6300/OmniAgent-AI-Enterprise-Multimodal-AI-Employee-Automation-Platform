import hashlib
import hmac
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.approval import Approval


class ApprovalService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def decide(self, approval_id: UUID, user_id: UUID, decision: str, reason: str = None) -> Approval:
        approval = await self.session.get(Approval, approval_id)
        if not approval:
            raise ValueError("Approval not found")
        
        approval.status = decision
        approval.decided_by = user_id
        approval.decision_reason = reason
        approval.decided_at = datetime.now(UTC)
        
        sig = hmac.new(
            settings.SECRET_KEY.encode(),
            f"{approval.id}:{decision}:{user_id}".encode(),
            hashlib.sha256
        ).hexdigest()
        approval.signature_hmac = sig
        
        await self.session.flush()
        return approval
