from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.action import (
    ActionApprovalRead,
    ActionApproveRequest,
    ActionExecuteRequest,
    ActionExecuteResponse,
    ActionHistoryItem,
    ActionRejectRequest,
)
from app.schemas.agent import (
    AgentRunRead,
    AgentRunRequest,
    SupervisorAnalyzeRequest,
    SupervisorDecision,
)
from app.schemas.common import ResponseEnvelope
from app.schemas.database import DatabaseQueryRequest, DatabaseResponse
from app.schemas.document import DocumentAnalysisResponseData, DocumentAnalyzeRequest
from app.schemas.rag import CitationData, RAGQueryRequest, RAGQueryResponseData
from app.schemas.reasoning import (
    ReasoningAnalyzeRequest,
    ReasoningAnalyzeResponseData,
)
from app.schemas.vision import (
    VisionAnalysisResponseData,
    VisionAnalyzeRequest,
    VisionUploadResponse,
)
from app.services.action_service import ActionService
from app.services.agent_service import AgentService
from app.services.database_service import DatabaseService
from app.services.document_service import DocumentService
from app.services.rag_service import RAGService
from app.services.reasoning_service import ReasoningService
from app.services.vision_service import VisionService

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post("/run", response_model=ResponseEnvelope[AgentRunRead])
async def run_agent(
    request: AgentRunRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Executes a specialist agent run (legacy / direct run)."""
    service = AgentService(session)
    run = await service.run_agent(current_user.id, current_user.organization_id, request)
    return ResponseEnvelope(data=run)


@router.post("/supervisor/analyze", response_model=ResponseEnvelope[SupervisorDecision])
async def analyze_supervisor_request(
    request: SupervisorAnalyzeRequest,
    http_req: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Central cognitive routing analysis by Supervisor Agent.
    Classifies intent, selects target specialized agent, evaluates approval/tool requirements,
    and returns a structured operational task plan.
    """
    request_id = getattr(http_req.state, "request_id", None)
    service = AgentService(session)
    decision = await service.analyze_supervisor(
        user_id=current_user.id,
        org_id=current_user.organization_id,
        request=request,
        request_id=request_id,
    )
    return ResponseEnvelope(data=decision)


@router.post("/document/analyze", response_model=ResponseEnvelope[DocumentAnalysisResponseData])
async def analyze_document_request(
    request: DocumentAnalyzeRequest,
    http_req: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Executes Document Agent deep parsing, classification, summarization, and structured extraction.
    Validates tenant organization access and operates upon previously stored document artifacts.
    """
    request_id = getattr(http_req.state, "request_id", None)
    service = DocumentService(session)
    analysis = await service.analyze_document(
        user_id=current_user.id,
        org_id=current_user.organization_id,
        request=request,
        request_id=request_id,
    )
    return ResponseEnvelope(data=analysis.model_dump())


@router.post("/rag/query", response_model=ResponseEnvelope[RAGQueryResponseData])
async def query_rag_agent(
    request: RAGQueryRequest,
    http_req: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Executes RAG Agent semantic retrieval and grounded answer generation.
    Retrieves vector passages strictly within the user's organization boundary.
    """
    request_id = getattr(http_req.state, "request_id", None)
    service = RAGService(session)
    response = await service.query(
        user_id=current_user.id,
        org_id=current_user.organization_id,
        question=request.question,
        document_id=request.document_id,
        top_k=request.top_k,
        request_id=request_id,
    )
    data = RAGQueryResponseData(
        answer=response.answer,
        grounded=response.grounded,
        confidence=response.confidence,
        citations=[CitationData(**c.model_dump()) for c in response.citations],
        retrieved_chunks=response.retrieved_chunks,
    )
    return ResponseEnvelope(data=data)


@router.post("/database/query", response_model=ResponseEnvelope[DatabaseResponse])
async def query_database_agent(
    request: DatabaseQueryRequest,
    http_req: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Executes Database Agent natural-language queries against authorized business data.
    Enforces multi-tenant isolation, approved schema allowlists, and parameterized read-only execution.
    """
    request_id = getattr(http_req.state, "request_id", None)
    service = DatabaseService(session)
    response = await service.query(
        user_id=current_user.id,
        org_id=current_user.organization_id,
        request=request,
        request_id=request_id,
    )
    return ResponseEnvelope(data=response)


@router.post(
    "/vision/upload",
    response_model=ResponseEnvelope[VisionUploadResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_vision_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Uploads and validates an image artifact (JPEG, PNG, WEBP) under the authenticated organization.
    Enforces format signatures, decompression safeguards, and tenant isolation.
    """
    service = VisionService(session)
    uploaded = await service.upload_image(
        user_id=current_user.id, org_id=current_user.organization_id, file=file
    )
    return ResponseEnvelope(data=uploaded)


@router.post("/vision/analyze", response_model=ResponseEnvelope[VisionAnalysisResponseData])
async def analyze_vision_image(
    request: VisionAnalyzeRequest,
    http_req: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Executes Vision Agent inspection, OCR extraction, object detection, and visual reasoning.
    Validates tenant organization access and operates upon previously stored image artifacts.
    """
    request_id = getattr(http_req.state, "request_id", None)
    service = VisionService(session)
    analysis = await service.analyze_image(
        user_id=current_user.id,
        org_id=current_user.organization_id,
        request=request,
        request_id=request_id,
    )
    return ResponseEnvelope(data=analysis.model_dump())


@router.get("/vision/images", response_model=ResponseEnvelope[list[VisionUploadResponse]])
async def list_vision_images(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Lists all image artifacts belonging to the authenticated tenant."""
    service = VisionService(session)
    images = await service.list_images(current_user.organization_id, skip=skip, limit=limit)
    return ResponseEnvelope(data=images)


@router.get("/vision/images/{image_id}", response_model=ResponseEnvelope[VisionUploadResponse])
async def get_vision_image(
    image_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieves image artifact metadata with strict tenant boundary enforcement."""
    service = VisionService(session)
    img = await service.get_image(image_id, current_user.organization_id)
    return ResponseEnvelope(data=img)


@router.post("/reasoning/analyze", response_model=ResponseEnvelope[ReasoningAnalyzeResponseData])
async def analyze_reasoning_request(
    request: ReasoningAnalyzeRequest,
    http_req: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Executes Reasoning Agent multi-step, multi-source grounded analysis.
    Orchestrates specialized downstream agents across databases, documents, knowledge bases,
    and visual inspection with strict tenant isolation and no chain-of-thought exposure.
    """
    request_id = getattr(http_req.state, "request_id", None)
    service = ReasoningService(session)
    response = await service.analyze(
        user_id=current_user.id,
        org_id=current_user.organization_id,
        request=request,
        request_id=request_id,
    )
    return ResponseEnvelope(data=response.model_dump())


@router.post("/action/execute", response_model=ResponseEnvelope[ActionExecuteResponse])
async def execute_action_request(
    request: ActionExecuteRequest,
    http_req: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Executes an authorized enterprise action or initiates a human-in-the-loop approval request.
    Strictly tenant-isolated; verifies parameters, idempotency, and risk classification.
    """
    request_id = getattr(http_req.state, "request_id", None)
    client_ip = http_req.client.host if http_req.client else None
    user_role = current_user.role.name if current_user.role else "Operator"
    user_perms = [p.name for p in current_user.role.permissions] if (current_user.role and current_user.role.permissions) else []

    service = ActionService(session)
    result = await service.execute_action(
        user_id=current_user.id,
        org_id=current_user.organization_id,
        user_role=user_role,
        user_perms=user_perms,
        request=request,
        request_id=request_id,
        ip_address=client_ip,
    )
    return ResponseEnvelope(data=result)


@router.get("/action/approvals", response_model=ResponseEnvelope[list[ActionApprovalRead]])
async def list_action_approvals(
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Lists pending, approved, or rejected action approvals strictly within the user's organization.
    """
    service = ActionService(session)
    approvals = await service.list_approvals(
        org_id=current_user.organization_id,
        status_filter=status,
        skip=skip,
        limit=limit,
    )
    return ResponseEnvelope(data=[ActionApprovalRead.model_validate(a) for a in approvals])


@router.post("/action/approvals/{approval_id}/approve", response_model=ResponseEnvelope[ActionApprovalRead])
async def approve_action_request(
    approval_id: UUID,
    request: ActionApproveRequest = ActionApproveRequest(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Approves a pending action request and immediately dispatches execution.
    Requires appropriate approval permissions.
    """
    user_role = current_user.role.name if current_user.role else "Operator"
    user_perms = [p.name for p in current_user.role.permissions] if (current_user.role and current_user.role.permissions) else []

    service = ActionService(session)
    approval, _ = await service.approve_action(
        approval_id=approval_id,
        user_id=current_user.id,
        org_id=current_user.organization_id,
        user_role=user_role,
        user_perms=user_perms,
        reason=request.reason,
    )
    return ResponseEnvelope(data=ActionApprovalRead.model_validate(approval))


@router.post("/action/approvals/{approval_id}/reject", response_model=ResponseEnvelope[ActionApprovalRead])
async def reject_action_request(
    approval_id: UUID,
    request: ActionRejectRequest = ActionRejectRequest(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Rejects a pending action approval request.
    Requires appropriate approval permissions.
    """
    user_role = current_user.role.name if current_user.role else "Operator"
    user_perms = [p.name for p in current_user.role.permissions] if (current_user.role and current_user.role.permissions) else []

    service = ActionService(session)
    approval = await service.reject_action(
        approval_id=approval_id,
        user_id=current_user.id,
        org_id=current_user.organization_id,
        user_role=user_role,
        user_perms=user_perms,
        reason=request.reason,
    )
    return ResponseEnvelope(data=ActionApprovalRead.model_validate(approval))


@router.get("/action/history", response_model=ResponseEnvelope[list[ActionHistoryItem]])
async def get_action_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Retrieves execution history of enterprise actions scoped to the organization.
    """
    service = ActionService(session)
    history = await service.get_history(
        org_id=current_user.organization_id,
        skip=skip,
        limit=limit,
    )
    return ResponseEnvelope(data=[ActionHistoryItem.model_validate(h) for h in history])
