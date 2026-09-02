from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.rag.retrieval.vector_search import VectorSearch

class HybridSearch:
    def __init__(self, session: AsyncSession):
        self.vector_search = VectorSearch(session)

    async def search(self, org_id: UUID, query_text: str, query_embedding: List[float], top_k: int = 5):
        # Combines dense vector search with sparse keyword search
        return await self.vector_search.search(org_id, query_embedding, top_k)
