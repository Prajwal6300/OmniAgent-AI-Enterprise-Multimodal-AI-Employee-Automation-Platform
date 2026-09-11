from datetime import UTC, datetime
from uuid import UUID

from agents.document.agent import DocumentAgent
from agents.document.schemas import DocumentAnalysisResult
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentAnalyzeRequest
from app.services.storage_service import BaseStorageService, get_storage_service


class DocumentService:
    def __init__(
        self,
        session: AsyncSession,
        storage_service: BaseStorageService | None = None,
        document_agent: DocumentAgent | None = None
    ):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.storage = storage_service or get_storage_service()
        self.agent = document_agent or DocumentAgent()

    async def list_documents(self, org_id: UUID, skip: int = 0, limit: int = 50) -> list[Document]:
        """Lists documents strictly scoped to the requesting organization."""
        return await self.doc_repo.list_by_org(org_id, skip=skip, limit=limit)

    async def get_document(self, doc_id: UUID, org_id: UUID) -> Document:
        """Retrieves a document with strict tenant boundary enforcement."""
        doc = await self.doc_repo.get_by_id_and_org(doc_id, org_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found in this organization."
            )
        return doc

    async def upload_document(
        self,
        user_id: UUID,
        org_id: UUID,
        file: UploadFile
    ) -> Document:
        """
        Validates, persists to storage, and records document metadata with tenant isolation.
        """
        filename = file.filename or "uploaded_document.bin"
        content_type = file.content_type or "application/octet-stream"

        # Read and validate file content
        file_bytes = await file.read()
        if not file_bytes or len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty (0 bytes)."
            )

        if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024):.1f} MB."
            )

        # Enforce supported extensions
        lower_name = filename.lower()
        if not any(lower_name.endswith(ext) for ext in [".pdf", ".docx", ".txt"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported document type. Only PDF (.pdf), Word (.docx), and Text (.txt) files are supported."
            )

        # Persist through storage service
        try:
            storage_path, checksum, file_size = await self.storage.save_file(
                file_data=file_bytes,
                original_filename=filename,
                org_id=org_id
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("document_storage_failed", error=str(exc), filename=filename, org_id=str(org_id))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to persist file in storage: {exc!s}"
            )

        now = datetime.now(UTC)
        doc = Document(
            organization_id=org_id,
            uploaded_by=user_id,
            file_name=filename,
            file_path=storage_path,
            file_type=content_type,
            file_size_bytes=file_size,
            checksum_sha256=checksum,
            processing_status="UPLOADED",
            created_at=now,
            updated_at=now,
            metadata_={
                "original_filename": filename,
                "mime_type": content_type,
                "extension": lower_name.split(".")[-1],
                "indexing_status": "NOT_INDEXED"
            }
        )
        created_doc = await self.doc_repo.create(doc)
        logger.info(
            "document_uploaded",
            document_id=str(created_doc.id),
            organization_id=str(org_id),
            user_id=str(user_id),
            file_name=filename,
            file_size=file_size
        )
        return created_doc

    async def analyze_document(
        self,
        user_id: UUID,
        org_id: UUID,
        request: DocumentAnalyzeRequest,
        request_id: str | None = None
    ) -> DocumentAnalysisResult:
        """
        Executes document intelligence pipeline on an existing document for an authorized tenant.
        """
        doc = await self.get_document(request.document_id, org_id)

        # Update status to PROCESSING
        await self.doc_repo.update_status(doc.id, "PROCESSING")

        # Read content from storage
        try:
            file_bytes = await self.storage.read_file(doc.file_path)
        except Exception as exc:  # noqa: BLE001
            await self.doc_repo.update_status(doc.id, "FAILED", {"error": f"Storage read error: {exc!s}"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read file from storage: {exc!s}"
            )

        # Run Document Agent LangGraph workflow
        result = await self.agent.analyze(
            document_id=str(doc.id),
            file_bytes=file_bytes,
            file_path=doc.file_path,
            filename=doc.file_name,
            mime_type=doc.file_type,
            task=request.task,
            query=request.query,
            user_id=str(user_id),
            organization_id=str(org_id),
            request_id=request_id
        )

        final_status = "PROCESSED" if result.confidence > 0.0 and not result.title.startswith("Error") else "FAILED"
        metadata_update = {
            "document_type": result.document_type,
            "title": result.title,
            "confidence": result.confidence,
            "needs_ocr": result.needs_ocr,
            "analysis": result.model_dump(),
            "indexing_status": "NOT_INDEXED"
        }
        await self.doc_repo.update_status(doc.id, final_status, metadata_update)

        # Trigger RAG Ingestion Pipeline upon successful document processing
        if final_status == "PROCESSED" and result.pages:
            try:
                from app.services.rag.ingestion.pipeline import RAGIngestionPipeline
                pipeline = RAGIngestionPipeline(self.session)
                pages_data = [p.model_dump() for p in result.pages]
                await pipeline.index_document(doc, pages=pages_data)
            except Exception as index_err:
                logger.error(
                    "rag_indexing_trigger_failed",
                    document_id=str(doc.id),
                    organization_id=str(org_id),
                    error=str(index_err)
                )

        return result

    async def index_document(self, doc_id: UUID, org_id: UUID) -> int:
        """
        Manually triggers RAG indexing for an existing document in this organization.
        """
        doc = await self.get_document(doc_id, org_id)
        from app.services.rag.ingestion.pipeline import RAGIngestionPipeline
        pipeline = RAGIngestionPipeline(self.session)
        return await pipeline.index_document(doc)
