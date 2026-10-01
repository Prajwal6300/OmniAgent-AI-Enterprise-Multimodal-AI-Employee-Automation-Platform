from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import DocumentChunk


class VectorSearch:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(
        self,
        org_id: UUID,
        query_embedding: list[float],
        query_text: str = "",
        top_k: int = 5,
        search_mode: str = "dense",
    ) -> list[DocumentChunk]:
        """Search document chunks with mode: 'dense' or 'hybrid'.

        - dense: pgvector cosine distance only, tenant-filtered
        - hybrid: pgvector + tsvector (GIN) + Reciprocal Rank Fusion (k=60), tenant-filtered
        """
        if search_mode == "dense":
            return await self._dense_search(org_id, query_embedding, top_k)

        if search_mode == "hybrid":
            return await self._hybrid_search(org_id, query_embedding, query_text=query_text, top_k=top_k)

        return await self._dense_search(org_id, query_embedding, top_k)

    async def _dense_search(
        self, org_id: UUID, query_embedding: list[float], top_k: int
    ) -> list[DocumentChunk]:
        """Dense vector search using pgvector cosine distance."""
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.organization_id == org_id)
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _hybrid_search(
        self, org_id: UUID, query_embedding: list[float], query_text: str, top_k: int
    ) -> list[DocumentChunk]:
        """Hybrid search: dense pgvector + sparse tsvector + Reciprocal Rank Fusion (k=60)."""

        # Step 1: Dense vector search (top 200 candidates)
        dense_stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.organization_id == org_id)
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(200)
        )
        dense_result = await self.session.execute(dense_stmt)
        dense_chunks = list(dense_result.scalars().all())

        if not dense_chunks:
            return []

        # Step 2: Sparse tsearch search (GIN on generated tsvector column)
        # Build a plain SQL query for tsvector similarity since we need rank function
        # We'll use a raw SQL approach for RRF since SQLAlchemy doesn't directly support it
        tsvector_qs = (
            select(
                DocumentChunk,
                func.ts_rank_cd(
                    func.to_tsvector('english', DocumentChunk.content),
                    func.plainto_tsquery('english', query_text or ""),
                ).label("ts_rank"),
            )
            .where(DocumentChunk.organization_id == org_id)
            .order_by(
                func.ts_rank_cd(
                    func.to_tsvector('english', DocumentChunk.content),
                    func.plainto_tsquery('english', query_text or ""),
                ).desc()
            )
            .limit(200)
        )
        tsvector_result = await self.session.execute(tsvector_qs)
        tsvector_chunks = list(tsvector_result.unique(DocumentChunk).scalars().all())

        if not tsvector_chunks:
            # Fall back to dense only
            return dense_chunks[:top_k]

        # Step 3: Reciprocal Rank Fusion (k=60)
        # Rank chunks from both sources and fuse scores
        rrf_k = 60

        # Get ranks for dense results
        dense_scores = {}
        for rank, chunk in enumerate(dense_chunks, start=1):
            chunk_id = chunk.id
            if chunk_id:
                dense_scores[chunk_id] = rank

        # Get ranks for tsvector results
        tsvector_scores = {}
        for rank, chunk in enumerate(tsvector_chunks, start=1):
            chunk_id = chunk.id
            if chunk_id:
                tsvector_scores[chunk_id] = rank

        # Fusion: combine scores from both sources
        fused_scores: dict[UUID, float] = {}

        for chunk_id, rank in dense_scores.items():
            if rank > 0:
                fused_scores[chunk_id] = fused_scores.get(chunk_id, 0) + 1 / (rrf_k + rank)

        for chunk_id, rank in tsvector_scores.items():
            if rank > 0:
                fused_scores[chunk_id] = fused_scores.get(chunk_id, 0) + 1 / (rrf_k + rank)

        # Sort by fused score and return top_k
        sorted_chunk_ids = sorted(fused_scores.keys(), key=lambda cid: fused_scores[cid], reverse=True)

        # Retrieve full chunk objects for the top-k fused results
        if not sorted_chunk_ids:
            return dense_chunks[:top_k]

        # Get chunks by ID
        set(sorted_chunk_ids[:top_k * 2])  # Get extra in case some are missing
        chunk_lookup = {chunk.id: chunk for chunk in dense_chunks}

        # Add tsvector chunks to lookup
        for chunk in tsvector_chunks:
            chunk_lookup[chunk.id] = chunk

        result_chunks = [chunk_lookup[cid] for cid in sorted_chunk_ids[:top_k] if cid in chunk_lookup]

        return result_chunks[:top_k]