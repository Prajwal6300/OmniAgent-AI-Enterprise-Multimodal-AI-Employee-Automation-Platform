"""
Vision Schemas for API Serialization.
Defines request and response schemas for image upload,
analysis invocation, and structured inspection results.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VisionAnalyzeRequest(BaseModel):
    """Payload for invoking Vision Agent analysis on an uploaded image artifact."""

    image_id: UUID = Field(..., description="UUID of the uploaded image to analyze")
    question: str = Field(
        ..., description="Natural language question, inspection inquiry, or instruction"
    )
    task_type: str | None = Field(
        default=None,
        description="Optional task classification: VISUAL_INSPECTION, DAMAGE_ANALYSIS, COMPONENT_IDENTIFICATION, OCR, TEXT_EXTRACTION, SAFETY_ANALYSIS, OBJECT_DETECTION, GENERAL_IMAGE_ANALYSIS",
    )


class VisionUploadResponse(BaseModel):
    """Metadata returned upon successful image upload."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    organization_id: UUID
    uploaded_by: UUID | None = None
    file_name: str
    file_type: str
    file_size_bytes: int
    checksum_sha256: str
    width: int
    height: int
    processing_status: str
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(UTC))


class VisionAnalysisResponseData(BaseModel):
    """Structured response data returned from Vision Agent execution."""

    request_id: str
    image_id: str
    task_type: str
    question: str
    summary: str
    answer: str
    findings: list[dict[str, Any]] = Field(default_factory=list)
    detected_objects: list[dict[str, Any]] = Field(default_factory=list)
    ocr_result: dict[str, Any] = Field(default_factory=dict)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 1.0
    image_metadata: dict[str, Any] = Field(default_factory=dict)
    component_statuses: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    execution_time_ms: float | None = None
