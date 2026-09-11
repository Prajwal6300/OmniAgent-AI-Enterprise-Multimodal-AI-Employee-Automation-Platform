from typing import Any, List, Optional
from uuid import UUID
from datetime import datetime, UTC
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk
from app.services.rag.embeddings.factory import EmbeddingFactory
from app.services.rag.ingestion.chunker import TextChunker
from app.services.rag.ingestion.loader import DocumentLoader
from app.services.rag.ingestion.metadata import MetadataExtractor
from app.core.logging import logger


class IngestionPipeline:
    """Legacy helper pipeline maintained for compatibility."""
    def __init__(self):
        self.loader = DocumentLoader()
        self.chunker = TextChunker()
        self.metadata_extractor = MetadataExtractor()

    def run(self, file_path: str):
        docs = self.loader.load(file_path)
        chunks = []
        for doc in docs:
            raw_chunks = self.chunker.chunk(doc["text"])
            for idx, text in enumerate(raw_chunks):
                meta = self.metadata_extractor.enrich(text, doc)
                chunks.append({"index": idx, "content": text, "metadata": meta})
        return chunks


class RAGIngestionPipeline:
    """
    Production-grade RAG Ingestion Pipeline.
    Transforms processed document pages into indexed semantic chunks in PostgreSQL + pgvector.
    Preserves page boundaries, sections, and tenant isolation tags.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.chunker = TextChunker()
        self.embedding_provider = EmbeddingFactory.get_provider()

    async def index_document(
        self,
        document: Document,
        pages: Optional[List[dict[str, Any]]] = None,
        sections: Optional[List[dict[str, Any]]] = None,
        raw_text: Optional[str] = None
    ) -> int:
        """
        Indexes a document into pgvector chunks.
        Updates indexing status from NOT_INDEXED -> INDEXING -> INDEXED.
        """
        doc_id = document.id
        org_id = document.organization_id
        file_name = document.file_name

        # 1. Update status to INDEXING
        meta = dict(document.metadata_ or {})
        meta["indexing_status"] = "INDEXING"
        document.metadata_ = meta
        await self.session.flush()

        try:
            # 2. Extract structured pages for chunking
            pages_to_chunk = pages or []
            if not pages_to_chunk and raw_text:
                pages_to_chunk = [{"page_number": 1, "text": raw_text}]
            elif not pages_to_chunk and meta.get("analysis", {}).get("pages"):
                pages_to_chunk = meta["analysis"]["pages"]

            if not pages_to_chunk:
                meta["indexing_status"] = "INDEXED"
                meta["indexed_chunks_count"] = 0
                document.metadata_ = meta
                await self.session.flush()
                return 0

            # 3. Create chunks preserving physical page numbers and sections
            chunks_data = self.chunker.chunk_pages(pages_to_chunk, sections=sections)
            if not chunks_data:
                meta["indexing_status"] = "INDEXED"
                meta["indexed_chunks_count"] = 0
                document.metadata_ = meta
                await self.session.flush()
                return 0

            # 4. Remove previous chunks for this document if re-indexing
            await self.session.execute(
                delete(DocumentChunk).where(
                    DocumentChunk.document_id == doc_id,
                    DocumentChunk.organization_id == org_id
                )
            )

            # 5. Batch generate embeddings for chunk contents
            texts_to_embed = [c["content"] for c in chunks_data]
            embeddings = await self.embedding_provider.embed_documents(texts_to_embed)

            # 6. Persist DocumentChunk records to database
            now = datetime.now(UTC)
            for idx, (c_data, emb) in enumerate(zip(chunks_data, embeddings)):
                token_count = len(c_data["content"].split())
                chunk_meta = {
                    "document_name": file_name,
                    "page_number": c_data.get("page_number"),
                    "section": c_data.get("section"),
                    "chunk_index": idx
                }
                chunk_record = DocumentChunk(
                    document_id=doc_id,
                    organization_id=org_id,
                    chunk_index=idx,
                    content=c_data["content"],
                    token_count=token_count,
                    embedding=emb,
                    metadata_=chunk_meta,
                    created_at=now
                )
                self.session.add(chunk_record)

            # 7. Update status to INDEXED
            meta["indexing_status"] = "INDEXED"
            meta["indexed_chunks_count"] = len(chunks_data)
            meta["indexed_at"] = now.isoformat()
            document.metadata_ = meta
            await self.session.flush()

            logger.info(
                "document_indexing_completed",
                document_id=str(doc_id),
                organization_id=str(org_id),
                chunks_indexed=len(chunks_data)
            )

            return len(chunks_data)

        except Exception as exc:
            logger.error(
                "document_indexing_failed",
                document_id=str(doc_id),
                organization_id=str(org_id),
                error=str(exc)
            )
            meta["indexing_status"] = "INDEX_FAILED"
            meta["indexing_error"] = str(exc)
            document.metadata_ = meta
            await self.session.flush()
            raise
