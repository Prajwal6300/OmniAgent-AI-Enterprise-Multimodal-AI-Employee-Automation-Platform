"""
OmniAgent AI — Approval Service
Enforces distributed locking, separation of duties, and dual-approver gating for CRITICAL risk actions.
"""

import hashlib
import hmac
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import distributed_lock
from app.models.approval import Approval

logger = structlog.get_logger(__name__)


class ApprovalService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def decide(
        self,
        approval_id: UUID,
        user_id: UUID,
        decision: str,
        reason: str | None = None,
    ) -> Approval:
        decision_upper = decision.upper()
        if decision_upper not in ("APPROVED", "REJECTED"):
            raise ValueError(f"Invalid decision '{decision}'. Must be APPROVED or REJECTED.")

        # Redis distributed lock prevents concurrent race conditions on the same approval
        async with distributed_lock(f"approval:{approval_id}", timeout_seconds=10):
            approval = await self.session.get(Approval, approval_id)
            if not approval:
                raise ValueError("Approval not found")

            if approval.status in ("REJECTED", "APPROVED"):
                raise ValueError(f"Approval is already finalized with status: {approval.status}")

            now = datetime.now(UTC)

            # Rejection immediately terminates regardless of risk level
            if decision_upper == "REJECTED":
                approval.status = "REJECTED"
                if not approval.decided_by:
                    approval.decided_by = user_id
                    approval.decided_at = now
                else:
                    approval.second_decided_by = user_id
                    approval.second_decided_at = now
                approval.decision_reason = reason
                approval.signature_hmac = self._sign_decision(approval.id, "REJECTED", user_id)
                await self.session.flush()
                return approval

            # Separation of duties: requesters cannot approve their own HIGH or CRITICAL requests
            if approval.risk_level in ("HIGH", "CRITICAL") and approval.requested_by and approval.requested_by == user_id:
                raise PermissionError(
                    f"Separation of duties violation: requester cannot approve {approval.risk_level} risk action"
                )

            # Dual-approver gating for CRITICAL actions
            if approval.risk_level == "CRITICAL":
                if approval.status == "PENDING" and not approval.decided_by:
                    # First approver recorded
                    approval.decided_by = user_id
                    approval.decided_at = now
                    approval.decision_reason = reason
                    approval.status = "PENDING_SECOND_APPROVAL"
                    approval.signature_hmac = self._sign_decision(approval.id, "PARTIAL_APPROVAL", user_id)
                    await self.session.flush()
                    return approval

                if approval.status == "PENDING_SECOND_APPROVAL":
                    # Second approver MUST be distinct from first approver
                    if approval.decided_by == user_id:
                        raise ValueError(
                            "Dual-approver policy: second approval must be granted by a different authorized approver"
                        )
                    approval.second_decided_by = user_id
                    approval.second_decided_at = now
                    approval.status = "APPROVED"
                    approval.signature_hmac = self._sign_decision(
                        approval.id, f"APPROVED:{approval.decided_by}:{user_id}", user_id
                    )
                    await self.session.flush()
                    return approval

            # Standard single approval for LOW, MEDIUM, HIGH actions
            approval.status = "APPROVED"
            approval.decided_by = user_id
            approval.decided_at = now
            approval.decision_reason = reason
            approval.signature_hmac = self._sign_decision(approval.id, "APPROVED", user_id)

            await self.session.flush()
            return approval

    def _sign_decision(self, approval_id: UUID, decision: str, user_id: UUID) -> str:
        raw = f"{approval_id}:{decision}:{user_id}".encode()
        return hmac.new(settings.SECRET_KEY.encode(), raw, hashlib.sha256).hexdigest()
