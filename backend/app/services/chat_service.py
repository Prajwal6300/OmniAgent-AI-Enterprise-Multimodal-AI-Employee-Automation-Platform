"""
OmniAgent AI — Chat Application Service
Coordinates conversational interactions, multi-agent orchestration invocation,
chat history persistence, citations, and human approvals.
"""

from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message
from app.orchestration.graph import Orchestrator
from app.orchestration.state import (
    ActionDetail,
    ApprovalDetail,
    CitationItem,
    EvidenceItem,
    ExecutionStepItem,
    UnifiedChatRequest,
    UnifiedChatResponse,
)
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.chat import MessageCreate


class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.conv_repo = ConversationRepository(session)
        self.orchestrator = Orchestrator()

    async def send_message(
        self,
        user_id: UUID,
        org_id: UUID,
        conv_id: UUID,
        payload: MessageCreate,
    ) -> Message:
        """Legacy conversation message persistence."""
        user_msg = Message(
            conversation_id=conv_id,
            sender_type="USER",
            content=payload.content,
        )
        await self.conv_repo.add_message(user_msg)
        return user_msg

    async def unified_chat(
        self,
        user_id: UUID,
        org_id: UUID,
        payload: UnifiedChatRequest,
        request_id: str | None = None,
    ) -> UnifiedChatResponse:
        """
        Unified endpoint orchestrating multi-agent reasoning, evidence collection,
        approvals, and conversational history persistence.
        """
        # 1. Resolve or create conversation
        conv_uuid = None
        if payload.conversation_id:
            try:
                conv_uuid = UUID(str(payload.conversation_id))
                existing_conv = await self.conv_repo.get_by_id(conv_uuid)
                if not existing_conv or existing_conv.organization_id != org_id:
                    conv_uuid = None
            except ValueError:
                conv_uuid = None

        if not conv_uuid:
            conv = Conversation(
                id=uuid4(),
                organization_id=org_id,
                user_id=user_id,
                title=payload.message[:50],
                agent_type="SUPERVISOR",
            )
            created_conv = await self.conv_repo.create_conversation(conv)
            conv_uuid = created_conv.id

        # 2. Persist user message
        user_msg = Message(
            id=uuid4(),
            conversation_id=conv_uuid,
            sender_type="USER",
            content=payload.message,
            metadata_={"attachments": [a.model_dump() for a in payload.attachments]},
        )
        await self.conv_repo.add_message(user_msg)

        # 3. Invoke multi-agent orchestration
        attachments_data = [a.model_dump() for a in payload.attachments]
        orch_state = await self.orchestrator.execute(
            message=payload.message,
            organization_id=str(org_id),
            user_id=str(user_id),
            conversation_id=str(conv_uuid),
            attachments=attachments_data,
            context=payload.context,
            session=self.session,
            request_id=request_id,
        )

        # 4. Extract citations and evidence
        citations = [
            CitationItem(**c) if isinstance(c, dict) else c
            for c in orch_state.get("citations", [])
        ]
        evidence = [
            EvidenceItem(**e) if isinstance(e, dict) else e
            for e in orch_state.get("evidence", [])
        ]
        steps = [
            ExecutionStepItem(**s) if isinstance(s, dict) else s
            for s in orch_state.get("execution_steps", [])
        ]

        action_obj = None
        act_res = orch_state.get("action_result")
        if act_res:
            action_obj = ActionDetail(
                action_id=act_res.get("action_id", ""),
                action_type=act_res.get("action_type", ""),
                status=act_res.get("status", ""),
                success=act_res.get("success", False),
                verified=act_res.get("verified", False),
                external_reference=act_res.get("external_reference"),
                message=act_res.get("message"),
                data=act_res.get("data"),
            )

        approval_obj = None
        appr_det = orch_state.get("approval_detail")
        if appr_det:
            approval_obj = ApprovalDetail(**appr_det)

        agents_used = [
            s.agent for s in steps if s.agent not in ("supervisor", "start")
        ]
        agents_used = sorted(set(agents_used))

        final_answer = orch_state.get("final_response") or "Analysis completed."
        status_str = orch_state.get("status", "COMPLETED")

        # 5. Persist agent reply
        agent_msg = Message(
            id=uuid4(),
            conversation_id=conv_uuid,
            sender_type="AGENT",
            content=final_answer,
            citations=[c.model_dump() for c in citations],
            metadata_={
                "status": status_str,
                "confidence": orch_state.get("confidence", 1.0),
                "agents_used": agents_used,
                "approval_id": orch_state.get("approval_id"),
            },
        )
        await self.conv_repo.add_message(agent_msg)

        return UnifiedChatResponse(
            request_id=orch_state.get("request_id", ""),
            conversation_id=str(conv_uuid),
            status=status_str,
            answer=final_answer,
            confidence=orch_state.get("confidence", 1.0),
            grounded=orch_state.get("grounded", True),
            citations=citations,
            evidence=evidence,
            agents_used=agents_used,
            execution_steps=steps,
            action=action_obj,
            approval=approval_obj,
            error=orch_state.get("error"),
        )
