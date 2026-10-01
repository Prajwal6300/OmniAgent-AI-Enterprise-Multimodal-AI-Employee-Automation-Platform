from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.rag.retrieval.reranking import get_reranker
from app.services.rag.retrieval.vector_search import VectorSearch


class HybridSearch:
    def __init__(self, session: AsyncSession):
        self.vector_search = VectorSearch(session)
        self.reranker = get_reranker()

    async def search(self, org_id: UUID, query_text: str, query_embedding: list[float], top_k: int = 5) -> list:
        """Search with reranking: retrieve top 20, rerank to top_k."""
        # Step 1: Retrieve top 20 from dense vector search
        retrieved_chunks = await self.vector_search.search(
            org_id, query_embedding, top_k=20
        )

        if not retrieved_chunks:
            return []

        # Step 2: Rerank to top_k
        reranked = await self.reranker.rerank(
            query=query_text,
            candidate_chunks=retrieved_chunks,
            top_k=top_k,
        )

        return reranked