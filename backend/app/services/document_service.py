from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.document_repository import DocumentRepository

class DocumentService:
    def __init__(self, session: AsyncSession):
        self.doc_repo = DocumentRepository(session)

    async def list_documents(self, org_id: UUID):
        return await self.doc_repo.list_by_org(org_id)
