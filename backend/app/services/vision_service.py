"""
Vision Service for OmniAgent AI.
Coordinates multi-tenant image persistence, storage isolation,
and Vision Agent execution across enterprise organizations.
"""

from datetime import UTC, datetime
from uuid import UUID

from agents.vision.agent import VisionAgent
from agents.vision.preprocessing import (
    safe_inspect_and_load,
    validate_image_metadata,
)
from agents.vision.schemas import VisionAnalysisResult
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.schemas.vision import VisionAnalyzeRequest, VisionUploadResponse
from app.services.storage_service import BaseStorageService, get_storage_service


class VisionService:
    """
    Business service layer managing vision artifact storage,
    tenant authorization, and invocation of the Vision Agent.
    """

    def __init__(
        self,
        session: AsyncSession,
        storage_service: BaseStorageService | None = None,
        vision_agent: VisionAgent | None = None,
    ):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.storage = storage_service or get_storage_service()
        self.agent = vision_agent or VisionAgent()

    async def upload_image(
        self, user_id: UUID, org_id: UUID, file: UploadFile
    ) -> VisionUploadResponse:
        """
        Validates, saves to isolated storage, and registers image artifact metadata in DB.
        Guarantees tenant isolation and protects against corrupt or malicious uploads.
        """
        filename = file.filename or "image.jpg"
        content_type = file.content_type or "image/jpeg"

        # 1. Read binary content
        file_bytes = await file.read()
        if not file_bytes or len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty (0 bytes)."
            )

        # 2. Strict file metadata and magic byte validation
        try:
            detected_format = validate_image_metadata(
                filename=filename, file_bytes=file_bytes, mime_type=content_type
            )
        except Exception as val_err:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))

        # 3. Inspect image dimensions and verify integrity
        try:
            pil_img = safe_inspect_and_load(file_bytes)
            width, height = pil_img.size
        except Exception as img_err:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Corrupted or invalid image data: {img_err!s}",
            )

        # 4. Save to tenant-isolated storage
        try:
            storage_path, checksum, file_size = await self.storage.save_file(
                file_data=file_bytes, original_filename=filename, org_id=org_id
            )
        except Exception as store_err:  # noqa: BLE001
            logger.error(
                "image_storage_failed", error=str(store_err), filename=filename, org_id=str(org_id)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to persist image in storage: {store_err!s}",
            )

        # 5. Persist document record with image metadata
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
                "artifact_type": "image",
                "width": width,
                "height": height,
                "format": detected_format,
                "original_filename": filename,
            },
        )
        created = await self.doc_repo.create(doc)
        logger.info(
            "image_uploaded_successfully",
            image_id=str(created.id),
            organization_id=str(org_id),
            filename=filename,
            dimensions=f"{width}x{height}",
            file_size_bytes=file_size,
        )

        return VisionUploadResponse(
            id=created.id,
            organization_id=created.organization_id,
            uploaded_by=created.uploaded_by,
            file_name=created.file_name,
            file_type=created.file_type,
            file_size_bytes=created.file_size_bytes,
            checksum_sha256=created.checksum_sha256,
            width=width,
            height=height,
            processing_status=created.processing_status,
            created_at=created.created_at,
        )

    async def get_image(self, image_id: UUID, org_id: UUID) -> VisionUploadResponse:
        """Retrieves image metadata strictly within tenant organization boundary."""
        doc = await self.doc_repo.get_by_id_and_org(image_id, org_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image {image_id} not found in this organization.",
            )

        meta = doc.metadata_ or {}
        return VisionUploadResponse(
            id=doc.id,
            organization_id=doc.organization_id,
            uploaded_by=doc.uploaded_by,
            file_name=doc.file_name,
            file_type=doc.file_type,
            file_size_bytes=doc.file_size_bytes,
            checksum_sha256=doc.checksum_sha256,
            width=meta.get("width", 0),
            height=meta.get("height", 0),
            processing_status=doc.processing_status,
            created_at=doc.created_at,
        )

    async def list_images(
        self, org_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[VisionUploadResponse]:
        """Lists image artifacts belonging to the authenticated tenant."""
        stmt = (
            select(Document)
            .where(Document.organization_id == org_id, Document.file_type.ilike("image/%"))
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        docs = list(result.scalars().all())

        responses = []
        for doc in docs:
            meta = doc.metadata_ or {}
            responses.append(
                VisionUploadResponse(
                    id=doc.id,
                    organization_id=doc.organization_id,
                    uploaded_by=doc.uploaded_by,
                    file_name=doc.file_name,
                    file_type=doc.file_type,
                    file_size_bytes=doc.file_size_bytes,
                    checksum_sha256=doc.checksum_sha256,
                    width=meta.get("width", 0),
                    height=meta.get("height", 0),
                    processing_status=doc.processing_status,
                    created_at=doc.created_at,
                )
            )
        return responses

    async def analyze_image(
        self,
        user_id: UUID,
        org_id: UUID,
        request: VisionAnalyzeRequest,
        request_id: str | None = None,
    ) -> VisionAnalysisResult:
        """
        Executes Vision Agent analysis on an image artifact strictly within the organization boundary.
        """
        # 1. Fetch document and enforce tenant isolation
        doc = await self.doc_repo.get_by_id_and_org(request.image_id, org_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image {request.image_id} not found in this organization.",
            )

        # 2. Update status to PROCESSING
        await self.doc_repo.update_status(doc.id, "PROCESSING")

        # 3. Read image bytes from secure storage
        try:
            image_bytes = await self.storage.read_file(doc.file_path)
        except Exception as read_err:  # noqa: BLE001
            await self.doc_repo.update_status(
                doc.id, "FAILED", {"error": f"Storage read error: {read_err!s}"}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read image from storage: {read_err!s}",
            )

        # 4. Invoke Vision Agent LangGraph pipeline
        result = await self.agent.analyze(
            image_id=str(doc.id),
            question=request.question,
            image_bytes=image_bytes,
            image_path=doc.file_path,
            filename=doc.file_name,
            mime_type=doc.file_type,
            task_type=request.task_type,
            user_id=str(user_id),
            organization_id=str(org_id),
            request_id=request_id,
        )

        final_status = "PROCESSED" if result.confidence > 0.0 else "FAILED"
        metadata_update = {
            "task_type": result.task_type,
            "confidence": result.confidence,
            "findings_count": len(result.findings),
            "detections_count": len(result.detected_objects),
            "ocr_text": result.ocr_result.text[:100] if result.ocr_result else "",
            "analysis": result.model_dump(),
        }
        await self.doc_repo.update_status(doc.id, final_status, metadata_update)

        return result
