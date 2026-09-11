from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from agents.rag.agent import RAGAgent
from agents.rag.embeddings import get_embedding_provider
from agents.rag.retriever import DatabaseVectorRetriever
from agents.rag.schemas import RAGResponse
from app.core.config import settings
from app.core.logging import logger
from app.models.agent_run import AgentRun
from app.repositories.agent_repository import AgentRepository
from app.repositories.document_repository import DocumentRepository


class RAGService:
    """
    Enterprise Application Service for RAG Agent.
    Enforces multi-tenant scoping, validates document permissions,
    bridges database pgvector retrieval, and logs audit metadata.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.agent_repo = AgentRepository(session)
        self.retriever = DatabaseVectorRetriever(session)
        self.embedding_provider = get_embedding_provider()
        self.agent = RAGAgent(
            embedding_provider=self.embedding_provider,
            retriever=self.retriever
        )

    async def query(
        self,
        user_id: UUID,
        org_id: UUID,
        question: str,
        document_id: Optional[str] = None,
        top_k: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> RAGResponse:
        """
        Executes tenant-isolated semantic search and grounded answer generation.
        """
        # Document-level permission and existence check
        doc_uuid = None
        if document_id:
            try:
                doc_uuid = UUID(str(document_id))
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid document UUID format: {document_id}"
                )

            # Enforce that the document belongs to the requesting tenant
            doc = await self.doc_repo.get_by_id_and_org(doc_uuid, org_id)
            if not doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document {document_id} not found in your organization."
                )

            # Check indexing status
            meta = doc.metadata_ or {}
            indexing_status = meta.get("indexing_status", "NOT_INDEXED")
            if indexing_status == "NOT_INDEXED":
                # Auto-index if document was already processed
                if doc.processing_status == "PROCESSED":
                    from app.services.rag.ingestion.pipeline import RAGIngestionPipeline
                    pipeline = RAGIngestionPipeline(self.session)
                    await pipeline.index_document(doc)
            elif indexing_status == "INDEX_FAILED":
                logger.warning(
                    "querying_failed_indexed_document",
                    document_id=str(doc.id),
                    org_id=str(org_id)
                )

        k = top_k or getattr(settings, "RAG_TOP_K", 5)

        # Run RAG Agent pipeline
        response = await self.agent.query(
            question=question,
            organization_id=str(org_id),
            user_id=str(user_id),
            document_id=str(doc_uuid) if doc_uuid else None,
            top_k=k,
            request_id=request_id
        )

        # Non-blocking audit log
        try:
            run = AgentRun(
                organization_id=org_id,
                user_id=user_id,
                agent_name="rag_agent",
                task_description=f"Query: {question[:200]}",
                status="COMPLETED" if response.grounded else "REFUSED"
            )
            await self.agent_repo.create_run(run)
        except Exception:
            pass

        return response
