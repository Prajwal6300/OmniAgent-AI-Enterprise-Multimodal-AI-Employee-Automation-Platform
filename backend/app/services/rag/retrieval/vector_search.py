from uuid import UUID
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import DocumentChunk

class VectorSearch:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(self, org_id: UUID, query_embedding: List[float], top_k: int = 5) -> List[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.organization_id == org_id)
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
