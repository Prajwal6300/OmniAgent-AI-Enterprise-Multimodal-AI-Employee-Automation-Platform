import math
from typing import Any, List, Optional
from uuid import UUID

from agents.rag.exceptions import RetrievalError, UnauthorizedDocumentAccessError
from agents.rag.schemas import RetrievedChunk

try:
    from sqlalchemy import select, and_
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.document import Document, DocumentChunk
except ImportError:
    AsyncSession = None
    Document = None
    DocumentChunk = None


class BaseRAGRetriever:
    """Base interface for RAG chunk retrieval with mandatory tenant isolation."""

    async def retrieve(
        self,
        query_embedding: List[float],
        organization_id: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        similarity_threshold: float = 0.05,
        user_id: Optional[str] = None
    ) -> List[RetrievedChunk]:
        raise NotImplementedError


class DatabaseVectorRetriever(BaseRAGRetriever):
    """
    Production vector retriever executing pgvector cosine distance queries against PostgreSQL.
    Enforces tenant isolation by organization_id in the database query clause.
    """

    def __init__(self, session: Any):
        self.session = session

    async def retrieve(
        self,
        query_embedding: List[float],
        organization_id: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        similarity_threshold: float = 0.05,
        user_id: Optional[str] = None
    ) -> List[RetrievedChunk]:
        if not self.session:
            raise RetrievalError("Database session is required for DatabaseVectorRetriever.")

        try:
            org_uuid = UUID(str(organization_id))
        except (ValueError, TypeError):
            raise UnauthorizedDocumentAccessError(f"Invalid organization UUID: {organization_id}")

        doc_uuid = None
        if document_id:
            try:
                doc_uuid = UUID(str(document_id))
            except (ValueError, TypeError):
                doc_uuid = None

        try:
            # Build query with join on Document to get document filename and verify tenant
            conditions = [DocumentChunk.organization_id == org_uuid]
            if doc_uuid:
                conditions.append(DocumentChunk.document_id == doc_uuid)

            # Cosine distance in pgvector: 0 is identical, 2 is opposite
            # Similarity = 1 - distance
            distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding)

            stmt = (
                select(DocumentChunk, Document.file_name, distance_expr.label("distance"))
                .join(Document, Document.id == DocumentChunk.document_id)
                .where(and_(*conditions))
                .order_by(distance_expr)
                .limit(top_k * 2)  # retrieve candidates for filtering
            )

            result = await self.session.execute(stmt)
            rows = result.all()

            retrieved: List[RetrievedChunk] = []
            for chunk_record, file_name, distance in rows:
                score = round(1.0 - float(distance), 4) if distance is not None else 0.5
                if score < similarity_threshold:
                    continue

                meta = chunk_record.metadata_ or {}
                retrieved.append(
                    RetrievedChunk(
                        chunk_id=str(chunk_record.id),
                        document_id=str(chunk_record.document_id),
                        organization_id=str(chunk_record.organization_id),
                        document_name=meta.get("document_name", file_name or "Document"),
                        page_number=meta.get("page_number"),
                        section=meta.get("section"),
                        chunk_index=chunk_record.chunk_index,
                        content=chunk_record.content,
                        similarity_score=score,
                        metadata=meta
                    )
                )

            return retrieved[:top_k]

        except Exception as exc:
            if isinstance(exc, (UnauthorizedDocumentAccessError, RetrievalError)):
                raise
            raise RetrievalError(f"PostgreSQL pgvector retrieval failed: {exc!s}") from exc


class InMemoryVectorRetriever(BaseRAGRetriever):
    """
    High-performance in-memory vector retriever for deterministic unit tests and offline fixtures.
    Implements exact cosine similarity and enforces tenant boundaries without requiring a live database.
    """

    def __init__(self, initial_chunks: Optional[List[RetrievedChunk]] = None):
        self._chunks: List[RetrievedChunk] = initial_chunks or []

    def add_chunk(self, chunk: RetrievedChunk, embedding: Optional[List[float]] = None):
        if embedding:
            chunk.metadata["embedding"] = embedding
        self._chunks.append(chunk)

    def clear(self):
        self._chunks.clear()

    async def retrieve(
        self,
        query_embedding: List[float],
        organization_id: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        similarity_threshold: float = 0.05,
        user_id: Optional[str] = None
    ) -> List[RetrievedChunk]:
        scored: List[tuple[float, RetrievedChunk]] = []

        q_norm = math.sqrt(sum(x * x for x in query_embedding))

        for c in self._chunks:
            # Enforce strict organization tenant isolation
            if str(c.organization_id) != str(organization_id):
                continue

            # Enforce document_id filter if specified
            if document_id and str(c.document_id) != str(document_id):
                continue

            emb = c.metadata.get("embedding")
            if not emb:
                score = c.similarity_score or 0.8
            else:
                c_norm = math.sqrt(sum(y * y for y in emb))
                dot = sum(x * y for x, y in zip(query_embedding, emb))
                if q_norm > 0 and c_norm > 0:
                    score = round(dot / (q_norm * c_norm), 4)
                else:
                    score = c.similarity_score or 0.8

            if score >= similarity_threshold:
                # Clone with updated score
                updated = RetrievedChunk(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    organization_id=c.organization_id,
                    document_name=c.document_name,
                    page_number=c.page_number,
                    section=c.section,
                    chunk_index=c.chunk_index,
                    content=c.content,
                    similarity_score=score,
                    metadata=dict(c.metadata)
                )
                scored.append((score, updated))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]


class AgentRetriever:
    """
    Backward-compatibility class matching existing agent.py import.
    """
    def __init__(self, retriever: Optional[BaseRAGRetriever] = None):
        self._retriever = retriever or InMemoryVectorRetriever()

    async def retrieve(self, query: str, top_k: int = 5) -> List[dict]:
        # Legacy stub return format
        return [
            {"id": "doc-1", "snippet": "Enterprise standard operating procedure", "content": "Enterprise standard operating procedure"}
        ]
