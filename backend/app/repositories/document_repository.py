from uuid import UUID
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document

class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_org(self, org_id: UUID, skip: int = 0, limit: int = 50) -> List[Document]:
        stmt = select(Document).where(Document.organization_id == org_id).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, doc_id: UUID) -> Optional[Document]:
        stmt = select(Document).where(Document.id == doc_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, doc: Document) -> Document:
        self.session.add(doc)
        await self.session.flush()
        return doc
