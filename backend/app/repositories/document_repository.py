from uuid import UUID
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document

class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_org(self, org_id: UUID, skip: int = 0, limit: int = 50) -> List[Document]:
        stmt = select(Document).where(Document.organization_id == org_id).order_by(Document.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, doc_id: UUID) -> Optional[Document]:
        stmt = select(Document).where(Document.id == doc_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_org(self, doc_id: UUID, org_id: UUID) -> Optional[Document]:
        """Strict tenant-isolated document lookup."""
        stmt = select(Document).where(Document.id == doc_id, Document.organization_id == org_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, doc: Document) -> Document:
        self.session.add(doc)
        await self.session.flush()
        return doc

    async def update(self, doc: Document) -> Document:
        self.session.add(doc)
        await self.session.flush()
        return doc

    async def update_status(
        self,
        doc_id: UUID,
        status: str,
        metadata_update: Optional[Dict[str, Any]] = None
    ) -> Optional[Document]:
        doc = await self.get_by_id(doc_id)
        if not doc:
            return None
        doc.processing_status = status
        if metadata_update:
            current_meta = dict(doc.metadata_ or {})
            current_meta.update(metadata_update)
            doc.metadata_ = current_meta
        await self.session.flush()
        return doc
