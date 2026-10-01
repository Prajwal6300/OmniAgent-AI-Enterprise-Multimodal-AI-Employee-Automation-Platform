"""
Vision Agent Schemas.
Defines strongly typed Pydantic models for vision requests, task classification,
OCR extraction, object detection, visual findings, evidence grounding, and analysis results.
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class TaskType(str, Enum):
    """Supported Vision Task Classifications."""

    GENERAL_IMAGE_ANALYSIS = "GENERAL_IMAGE_ANALYSIS"
    OBJECT_DETECTION = "OBJECT_DETECTION"
    OCR = "OCR"
    TEXT_EXTRACTION = "TEXT_EXTRACTION"
    IMAGE_CLASSIFICATION = "IMAGE_CLASSIFICATION"
    VISUAL_INSPECTION = "VISUAL_INSPECTION"
    DAMAGE_ANALYSIS = "DAMAGE_ANALYSIS"
    COMPONENT_IDENTIFICATION = "COMPONENT_IDENTIFICATION"
    DOCUMENT_IMAGE_ANALYSIS = "DOCUMENT_IMAGE_ANALYSIS"
    SAFETY_ANALYSIS = "SAFETY_ANALYSIS"
    UNKNOWN = "UNKNOWN"


class ProcessorStatus(str, Enum):
    """Component capability and processing status."""

    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class VisionDetection(BaseModel):
    """Detected object with confidence and bounding coordinates."""

    label: str = Field(..., description="Detected object class or category")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score between 0 and 1"
    )
    bbox: list[float] | None = Field(
        default=None,
        description="Bounding box coordinates [ymin, xmin, ymax, xmax] or [x, y, w, h] in normalized or pixel coordinates",
    )
    description: str | None = Field(
        default=None,
        description="Optional descriptive detail about the detected entity",
    )

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, round(v, 4)))


class OCRRegion(BaseModel):
    """Extracted text segment with confidence and bounding box."""

    text: str = Field(..., description="Recognized text snippet")
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="OCR recognition confidence"
    )
    bbox: list[float] | None = Field(
        default=None,
        description="Bounding box [x, y, width, height] or [ymin, xmin, ymax, xmax]",
    )


class OCRResult(BaseModel):
    """Structured OCR extraction output."""

    text: str = Field(default="", description="Aggregated extracted textual content")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall OCR confidence score"
    )
    status: str = Field(
        default=ProcessorStatus.UNAVAILABLE.value, description="Processor status"
    )
    regions: list[OCRRegion] = Field(
        default_factory=list, description="Localized text bounding regions"
    )
    error: str | None = Field(
        default=None, description="Optional error or notice if OCR was unavailable"
    )


class VisualFinding(BaseModel):
    """Individual analytical finding derived from visual scene inspection."""

    title: str = Field(..., description="Finding title or summary point")
    description: str = Field(..., description="Detailed analytical description")
    severity: str | None = Field(
        default="INFO",
        description="Severity classification: INFO, LOW, MEDIUM, HIGH, CRITICAL",
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Finding confidence"
    )
    bbox: list[float] | None = Field(
        default=None, description="Optional focal bounding box region"
    )
    category: str | None = Field(
        default=None, description="Sub-category (e.g. defect, wear, label, structure)"
    )


class VisionCitation(BaseModel):
    """Grounding citation referencing visual evidence, bounding boxes, or OCR regions."""

    citation_id: str = Field(..., description="Unique citation reference ID")
    source_type: str = Field(
        ...,
        description="Evidence type: bounding_box, ocr_region, visual_finding, image_region",
    )
    label: str = Field(..., description="Label or entity name for the citation")
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Grounding confidence"
    )
    bbox: list[float] | None = Field(
        default=None, description="Evidence bounding box coordinates"
    )
    text: str | None = Field(
        default=None, description="Referenced text if derived from OCR"
    )
    details: str | None = Field(
        default=None, description="Supporting context or rationale"
    )


class ImageMetadata(BaseModel):
    """Image technical specifications."""

    width: int = Field(default=0, description="Image pixel width")
    height: int = Field(default=0, description="Image pixel height")
    format: str = Field(
        default="JPEG", description="Normalized image format (JPEG, PNG, WEBP)"
    )
    size_bytes: int = Field(default=0, description="Total byte size of the image")
    channels: int | None = Field(
        default=3, description="Color channels count (e.g. 3 for RGB)"
    )


class ComponentStatuses(BaseModel):
    """Health and availability report across sub-processors."""

    vision_model: str = Field(default=ProcessorStatus.AVAILABLE.value)
    ocr: str = Field(default=ProcessorStatus.AVAILABLE.value)
    object_detection: str = Field(default=ProcessorStatus.AVAILABLE.value)


class VisionAnalysisResult(BaseModel):
    """Comprehensive, grounded response model for Vision Agent execution."""

    request_id: str = Field(..., description="Unique execution request ID")
    image_id: str = Field(..., description="Referenced image UUID")
    task_type: str = Field(
        default=TaskType.GENERAL_IMAGE_ANALYSIS.value,
        description="Classified vision task",
    )
    question: str = Field(..., description="User prompt or analytical inquiry")
    summary: str = Field(
        default="", description="High-level summary of the visual findings"
    )
    answer: str = Field(
        ..., description="Factual, grounded natural language answer to the query"
    )
    findings: list[VisualFinding] = Field(
        default_factory=list, description="Structured visual findings"
    )
    detected_objects: list[VisionDetection] = Field(
        default_factory=list, description="Detected objects and classes"
    )
    ocr_result: OCRResult = Field(
        default_factory=OCRResult, description="OCR extraction data"
    )
    citations: list[VisionCitation] = Field(
        default_factory=list, description="Visual and textual evidence citations"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Overall analysis confidence score"
    )
    image_metadata: ImageMetadata = Field(
        default_factory=ImageMetadata, description="Image dimensions and metadata"
    )
    component_statuses: ComponentStatuses = Field(
        default_factory=ComponentStatuses, description="Processor statuses"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Operational warnings or limitation notes"
    )
    execution_time_ms: float | None = Field(
        default=None, description="Total execution latency in milliseconds"
    )

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, round(v, 4)))


# Backward-compatibility schema
class VisionResult(BaseModel):
    """Backward compatibility wrapper for legacy code."""

    observations: list[str] = Field(default_factory=list)
    detections: list[VisionDetection] = Field(default_factory=list)
