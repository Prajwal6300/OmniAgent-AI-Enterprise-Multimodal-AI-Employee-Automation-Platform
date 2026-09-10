from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.schemas.document import DocumentRead
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=ResponseEnvelope[DocumentRead], status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Uploads and validates a document (PDF, DOCX, TXT) under the authenticated organization.
    Saves file to secure storage with UUID sanitization and SHA-256 integrity checksum.
    """
    service = DocumentService(session)
    doc = await service.upload_document(
        user_id=current_user.id,
        org_id=current_user.organization_id,
        file=file
    )
    return ResponseEnvelope(data=doc)


@router.get("", response_model=ResponseEnvelope[list[DocumentRead]])
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Lists all documents belonging to the authenticated tenant.
    """
    service = DocumentService(session)
    docs = await service.list_documents(current_user.organization_id, skip=skip, limit=limit)
    return ResponseEnvelope(data=docs)


@router.get("/{document_id}", response_model=ResponseEnvelope[DocumentRead])
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Retrieves details and status of a specific document with tenant isolation check.
    """
    service = DocumentService(session)
    doc = await service.get_document(document_id, current_user.organization_id)
    return ResponseEnvelope(data=doc)
