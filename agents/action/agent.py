"""
OmniAgent AI — Action Agent
Primary cognitive actor responsible for executing authorized external side-effects,
enforcing human-in-the-loop approvals, tenant isolation, idempotency,
and immutable audit logging.
"""

import time
import uuid
from typing import Any

from app.core.logging import logger

from agents.action.action_policy import ActionPolicy
from agents.action.executor import ActionExecutor
from agents.action.graph import build_action_graph, run_sequential_flow
from agents.action.schemas import (
    ActionContext,
    ActionRequest,
    ActionResult,
    ActionStatus,
)
from agents.action.state import ActionState


class ActionAgent:
    """
    Action Agent for OmniAgent AI.
    Executes controlled business operations requested by users or reasoning outputs.
    Guarantees deny-by-default safety, human approvals for medium/high-risk actions,
    at-most-once idempotency, and tamper-evident audit logging.
    """

    def __init__(
        self,
        executor: ActionExecutor | None = None,
        session: Any = None,
        storage_service: Any = None,
    ):
        self.policy = ActionPolicy()
        self.executor = executor or ActionExecutor()
        self.session = session
        self.storage_service = storage_service
        self._compiled_graph = build_action_graph(
            executor=self.executor,
            session=self.session,
            storage_service=self.storage_service,
        )

    async def execute(
        self,
        request: ActionRequest,
        context: ActionContext,
        session: Any = None,
    ) -> ActionResult:
        """
        Main entrypoint executing an authorized enterprise action.
        Runs through full LangGraph pipeline:
        validate -> normalize -> permissions -> risk -> approval -> execute -> verify -> audit -> response.
        """
        start_time = time.time()
        active_session = session or self.session
        action_id = str(uuid.uuid4())
        req_id = context.request_id or str(uuid.uuid4())

        initial_state: ActionState = {
            "request_id": req_id,
            "user_id": context.user_id,
            "organization_id": context.organization_id,
            "user_role": context.user_role,
            "user_permissions": context.user_permissions,
            "conversation_id": context.conversation_id or str(uuid.uuid4()),
            "ip_address": context.ip_address,
            "action_id": action_id,
            "action_type": request.action_type,
            "input_data": request.input,
            "normalized_input": {},
            "risk_level": "LOW",
            "requires_approval": False,
            "approval_id": request.approval_id,
            "approval_status": "PENDING" if request.approval_id else "NOT_REQUIRED",
            "approval_binding_valid": False,
            "permission_check": False,
            "idempotency_key": request.idempotency_key,
            "idempotent_replay": False,
            "execution_status": ActionStatus.PENDING.value,
            "execution_result": {},
            "verification_status": "PENDING",
            "verification_result": {},
            "audit_id": "",
            "status": "INITIALIZED",
            "error": None,
            "response_message": "",
            "action_result": {},
            "task_plan": [],
            "latency_ms": None,
        }

        try:
            if self._compiled_graph is not None:
                final_state = await self._compiled_graph.ainvoke(initial_state)
            else:
                final_state = await run_sequential_flow(
                    initial_state,
                    executor=self.executor,
                    session=active_session,
                    storage_service=self.storage_service,
                )

            total_latency = round((time.time() - start_time) * 1000, 2)

            res_dict = final_state.get("action_result")
            if res_dict:
                if not res_dict.get("execution_time_ms"):
                    res_dict["execution_time_ms"] = total_latency
                result = ActionResult(**res_dict)
            else:
                result = ActionResult(
                    action_id=action_id,
                    action_type=request.action_type,
                    status=final_state.get("execution_status", ActionStatus.FAILED.value),
                    success=final_state.get("verification_status") == "VERIFIED",
                    message=final_state.get("response_message") or final_state.get("error", "Action terminated."),
                    verified=final_state.get("verification_status") == "VERIFIED",
                    requires_approval=final_state.get("requires_approval", False),
                    approval_id=final_state.get("approval_id"),
                    execution_time_ms=total_latency,
                )

            # Audit log completion event (safe metadata only, no secrets or tokens)
            logger.info(
                "action_agent_completed",
                action_id=result.action_id,
                action_type=result.action_type,
                org_id=context.organization_id,
                user_id=context.user_id,
                status=result.status,
                success=result.success,
                verified=result.verified,
                requires_approval=result.requires_approval,
                execution_time_ms=total_latency,
            )
            return result

        except Exception as exc:  # noqa: BLE001
            total_latency = round((time.time() - start_time) * 1000, 2)
            logger.error(
                "action_agent_execution_failed",
                action_id=action_id,
                action_type=request.action_type,
                org_id=context.organization_id,
                error=str(exc),
                execution_time_ms=total_latency,
            )
            return ActionResult(
                action_id=action_id,
                action_type=request.action_type,
                status=ActionStatus.FAILED.value,
                success=False,
                message=f"Action execution error: {exc!s}",
                verified=False,
                execution_time_ms=total_latency,
            )

    async def process(self, state: dict) -> dict:
        """Backward-compatible process method."""
        risk = self.policy.assess_risk("query_erp", {})
        return {"status": "success", "agent": "action", "risk_assessed": risk}
