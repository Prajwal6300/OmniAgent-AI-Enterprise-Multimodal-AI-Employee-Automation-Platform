"""
OmniAgent AI — Action Agent Application Service
Coordinates database persistence, tenant boundaries, Action Agent execution,
approval lifecycle transitions, and audit records.
"""

from datetime import UTC, datetime
from uuid import UUID

from agents.action.agent import ActionAgent
from agents.action.approval import (
    compute_approval_signature,
    compute_payload_hash,
    is_approval_expired,
)
from agents.action.schemas import (
    ActionContext,
    ActionRequest,
    ActionResult,
    ActionStatus,
    RiskLevel,
)
from agents.action.security import ActionSecurityGuard
from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.action import ActionApproval, ActionRecord
from app.schemas.action import (
    ActionExecuteRequest,
    ActionExecuteResponse,
)


class ActionService:
    """Enterprise service orchestrating action execution, approvals, and history."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute_action(
        self,
        user_id: UUID,
        org_id: UUID,
        user_role: str,
        user_perms: list[str],
        request: ActionExecuteRequest,
        request_id: str | None = None,
        ip_address: str | None = None,
    ) -> ActionExecuteResponse:
        """Executes an action request with full validation and tenant isolation."""
        context = ActionContext(
            user_id=str(user_id),
            organization_id=str(org_id),
            user_role=user_role,
            user_permissions=user_perms,
            request_id=request_id,
            ip_address=ip_address,
        )

        action_req = ActionRequest(
            action_type=request.action_type,
            input=request.input,
            reason=request.reason,
            idempotency_key=request.idempotency_key,
            approval_id=request.approval_id,
        )

        agent = ActionAgent(session=self.session)
        result: ActionResult = await agent.execute(
            request=action_req,
            context=context,
            session=self.session,
        )

        # If action executed immediately and succeeded, save ActionRecord
        if result.status == ActionStatus.COMPLETED.value:
            try:
                payload_hash = compute_payload_hash(
                    organization_id=str(org_id),
                    user_id=str(user_id),
                    action_type=request.action_type,
                    normalized_input=request.input,
                )
                action_rec = ActionRecord(
                    id=UUID(result.action_id),
                    organization_id=org_id,
                    requested_by=user_id,
                    action_type=result.action_type,
                    risk_level=RiskLevel.LOW.value,
                    status=result.status,
                    idempotency_key=request.idempotency_key,
                    input_hash=payload_hash,
                    input_payload=request.input,
                    result_payload=result.data,
                    external_reference=result.external_reference,
                    verified=result.verified,
                    completed_at=datetime.now(UTC),
                )
                self.session.add(action_rec)
                await self.session.flush()
            except Exception as exc:  # noqa: BLE001
                logger.warning("failed_saving_completed_action_record", error=str(exc))

        return ActionExecuteResponse(
            action_id=result.action_id,
            action_type=result.action_type,
            status=result.status,
            success=result.success,
            message=result.message,
            external_reference=result.external_reference,
            verified=result.verified,
            requires_approval=result.requires_approval,
            approval_id=result.approval_id,
            data=result.data,
            execution_time_ms=result.execution_time_ms,
        )

    async def list_approvals(
        self,
        org_id: UUID,
        status_filter: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ActionApproval]:
        """Lists approval requests scoped strictly to the authenticated organization."""
        query = select(ActionApproval).where(ActionApproval.organization_id == org_id)

        if status_filter:
            query = query.where(ActionApproval.status == status_filter.upper())

        query = query.order_by(desc(ActionApproval.created_at)).offset(skip).limit(limit)
        result = await self.session.execute(query)
        approvals = list(result.scalars().all())

        # Automatically check and mark expired approvals
        now = datetime.now(UTC)
        for appr in approvals:
            if appr.status == "PENDING" and is_approval_expired(appr.expires_at, now=now):
                appr.status = "EXPIRED"
                await self.session.flush()

        return approvals

    async def approve_action(
        self,
        approval_id: UUID,
        user_id: UUID,
        org_id: UUID,
        user_role: str,
        user_perms: list[str],
        reason: str | None = None,
    ) -> tuple[ActionApproval, ActionExecuteResponse | None]:
        """
        Approves an action request and executes it immediately using the verified token.
        Enforces tenant boundaries and cryptographic payload binding.
        """
        # 1. Authorization check
        if not ActionSecurityGuard.check_approval_permission(user_role, user_perms):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User lacks authorization to approve enterprise actions.",
            )

        # 2. Retrieve approval record
        approval = await self.session.get(ActionApproval, approval_id)
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval record '{approval_id}' not found.",
            )

        # 3. Enforce tenant isolation
        if approval.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot approve actions belonging to another organization.",
            )

        # 4. Check approval state
        if approval.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve action in status '{approval.status}'. Must be PENDING.",
            )

        # 5. Check expiration
        if is_approval_expired(approval.expires_at):
            approval.status = "EXPIRED"
            await self.session.flush()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Approval token has expired and cannot be approved.",
            )

        # 6. Apply approval state
        approval.status = "APPROVED"
        approval.approved_by = user_id
        approval.approved_at = datetime.now(UTC)
        approval.decision_reason = reason
        approval.signature_hmac = compute_approval_signature(
            approval_id=str(approval.id),
            decision="APPROVED",
            decider_user_id=str(user_id),
        )

        # 7. Update associated ActionRecord
        action_rec = await self.session.get(ActionRecord, approval.action_id)
        if action_rec:
            action_rec.status = ActionStatus.APPROVED.value
        await self.session.flush()

        # 8. Execute the approved action immediately
        exec_response = None
        if action_rec:
            agent = ActionAgent(session=self.session)
            context = ActionContext(
                user_id=str(approval.requested_by or user_id),
                organization_id=str(org_id),
                user_role=user_role,
                user_permissions=user_perms,
            )
            action_req = ActionRequest(
                action_type=approval.action_type,
                input=action_rec.input_payload,
                approval_id=str(approval.id),
            )
            exec_res = await agent.execute(action_req, context, session=self.session)

            # Update action record with final status
            action_rec.status = exec_res.status
            action_rec.result_payload = exec_res.data
            action_rec.external_reference = exec_res.external_reference
            action_rec.verified = exec_res.verified
            action_rec.completed_at = datetime.now(UTC)
            await self.session.flush()

            exec_response = ActionExecuteResponse(
                action_id=exec_res.action_id,
                action_type=exec_res.action_type,
                status=exec_res.status,
                success=exec_res.success,
                message=exec_res.message,
                external_reference=exec_res.external_reference,
                verified=exec_res.verified,
                requires_approval=False,
                approval_id=str(approval.id),
                data=exec_res.data,
                execution_time_ms=exec_res.execution_time_ms,
            )

        return approval, exec_response

    async def reject_action(
        self,
        approval_id: UUID,
        user_id: UUID,
        org_id: UUID,
        user_role: str,
        user_perms: list[str],
        reason: str | None = None,
    ) -> ActionApproval:
        """Rejects a pending action approval request with tenant isolation."""
        if not ActionSecurityGuard.check_approval_permission(user_role, user_perms):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User lacks authorization to reject enterprise actions.",
            )

        approval = await self.session.get(ActionApproval, approval_id)
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval record '{approval_id}' not found.",
            )

        if approval.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot reject actions belonging to another organization.",
            )

        if approval.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject action in status '{approval.status}'. Must be PENDING.",
            )

        approval.status = "REJECTED"
        approval.rejected_at = datetime.now(UTC)
        approval.decision_reason = reason
        approval.signature_hmac = compute_approval_signature(
            approval_id=str(approval.id),
            decision="REJECTED",
            decider_user_id=str(user_id),
        )

        action_rec = await self.session.get(ActionRecord, approval.action_id)
        if action_rec:
            action_rec.status = ActionStatus.REJECTED.value
            action_rec.completed_at = datetime.now(UTC)

        await self.session.flush()
        return approval

    async def get_history(
        self,
        org_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ActionRecord]:
        """Retrieves action execution history strictly within tenant boundaries."""
        query = (
            select(ActionRecord)
            .where(ActionRecord.organization_id == org_id)
            .order_by(desc(ActionRecord.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
