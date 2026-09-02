from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.document_service import DocumentService
from app.schemas.document import DocumentRead
from app.schemas.common import ResponseEnvelope

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.get("", response_model=ResponseEnvelope[List[DocumentRead]])
async def list_documents(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    service = DocumentService(session)
    docs = await service.list_documents(current_user.organization_id)
    return ResponseEnvelope(data=docs)
