"""
OmniAgent AI — Enterprise Reasoning Service
Application service coordinating multi-tenant authorization, conversation context reuse,
downstream agent execution, and audit logging for the Reasoning Agent.
"""

from uuid import UUID

from agents.reasoning.agent import ReasoningAgent
from agents.reasoning.executor import InternalAgentExecutor
from agents.reasoning.schemas import ReasoningResponse
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.models.agent_run import AgentRun
from app.models.document import Document
from app.repositories.agent_repository import AgentRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.reasoning import ReasoningAnalyzeRequest


class ReasoningService:
    """
    Enterprise Application Service for the Reasoning Agent.
    Guarantees strict tenant isolation, contextual image/document artifact resolution,
    and non-blocking operational audit telemetry.
    """

    def __init__(
        self,
        session: AsyncSession,
        reasoning_agent: ReasoningAgent | None = None,
    ):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.agent_repo = AgentRepository(session)

        # Build internal agent executor leveraging current db session
        executor = InternalAgentExecutor(
            default_timeout_seconds=float(
                getattr(settings, "REASONING_AGENT_TIMEOUT_SECONDS", 30.0)
            )
        )

        self.agent = reasoning_agent or ReasoningAgent(
            agent_executor=executor,
            max_depth=getattr(settings, "REASONING_MAX_AGENT_DEPTH", 3),
            max_agent_calls=getattr(settings, "REASONING_MAX_AGENT_CALLS", 5),
            timeout_seconds=float(getattr(settings, "REASONING_AGENT_TIMEOUT_SECONDS", 30.0)),
        )

    async def analyze(
        self,
        user_id: UUID,
        org_id: UUID,
        request: ReasoningAnalyzeRequest,
        request_id: str | None = None,
    ) -> ReasoningResponse:
        """
        Executes multi-source reasoning strictly scoped within the authenticated tenant boundary.
        Resolves previously uploaded conversation artifacts automatically.
        """
        resolved_image_id: str | None = None
        resolved_doc_id: str | None = None

        # 1. Explicit Image ID validation
        if request.image_id:
            img_doc = await self.doc_repo.get_by_id_and_org(request.image_id, org_id)
            if not img_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Image artifact {request.image_id} not found in this organization.",
                )
            resolved_image_id = str(img_doc.id)

        # 2. Explicit Document ID validation
        if request.document_id:
            doc_item = await self.doc_repo.get_by_id_and_org(request.document_id, org_id)
            if not doc_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document artifact {request.document_id} not found in this organization.",
                )
            resolved_doc_id = str(doc_item.id)

        # 3. Contextual Artifact Resolution: If query refers to an image or document but no ID passed
        q_lower = request.question.lower()
        if not resolved_image_id and any(
            k in q_lower for k in ["this image", "the image", "uploaded image", "inspection image"]
        ):
            # Resolve most recently uploaded image in this tenant
            stmt = (
                select(Document)
                .where(Document.organization_id == org_id, Document.file_type.ilike("image/%"))
                .order_by(Document.created_at.desc())
                .limit(1)
            )
            res = await self.session.execute(stmt)
            recent_img = res.scalar_one_or_none()
            if recent_img:
                resolved_image_id = str(recent_img.id)

        if not resolved_doc_id and any(
            k in q_lower
            for k in ["this document", "the manual", "uploaded manual", "troubleshooting manual"]
        ):
            # Resolve most recently uploaded document in this tenant
            stmt = (
                select(Document)
                .where(Document.organization_id == org_id, ~Document.file_type.ilike("image/%"))
                .order_by(Document.created_at.desc())
                .limit(1)
            )
            res = await self.session.execute(stmt)
            recent_doc = res.scalar_one_or_none()
            if recent_doc:
                resolved_doc_id = str(recent_doc.id)

        # 4. Prepare execution context
        exec_context = dict(request.context)
        exec_context["session"] = self.session
        exec_context["organization_id"] = str(org_id)
        exec_context["user_id"] = str(user_id)
        if request.conversation_id:
            exec_context["conversation_id"] = str(request.conversation_id)

        # 5. Run Reasoning Agent LangGraph pipeline
        response = await self.agent.analyze(
            question=request.question,
            organization_id=str(org_id),
            user_id=str(user_id),
            conversation_id=request.conversation_id,
            request_id=request_id,
            image_id=resolved_image_id,
            document_id=resolved_doc_id,
            context=exec_context,
        )

        # 6. Non-blocking audit logging into AgentRun table
        try:
            conv_uuid = None
            if request.conversation_id:
                try:
                    conv_uuid = UUID(request.conversation_id)
                except (ValueError, TypeError):
                    conv_uuid = None

            run = AgentRun(
                organization_id=org_id,
                user_id=user_id,
                conversation_id=conv_uuid,
                agent_name="reasoning_agent",
                task_description=request.question[:255],
                status="COMPLETED" if response.grounded else "FAILED",
            )
            await self.agent_repo.create_run(run)
        except Exception as audit_err:  # noqa: BLE001
            logger.warning("reasoning_agent_audit_log_failed", error=str(audit_err))

        return response
