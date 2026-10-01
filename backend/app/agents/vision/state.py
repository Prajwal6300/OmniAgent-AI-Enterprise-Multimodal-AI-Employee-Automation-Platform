"""
Vision State Definition.
Provides a strongly typed TypedDict representing the atomic execution state
flowing through the LangGraph Vision Agent pipeline.
"""

from typing import Any, TypedDict


class VisionState(TypedDict, total=False):
    """
    Strongly typed state dictionary for the Vision Agent LangGraph workflow.
    Adheres strictly to the enterprise multi-tenant execution model.
    """

    # Context & Tenant Metadata
    request_id: str
    user_id: str
    organization_id: str
    conversation_id: str

    # Image Identification & Raw Artifacts
    image_id: str
    filename: str
    mime_type: str
    image_bytes: bytes | None
    image_path: str
    preprocessed_image_path: str

    # Image Properties
    image_width: int
    image_height: int
    image_format: str
    image_size_bytes: int

    # Task & Analytical Query
    question: str
    task_type: str

    # OCR Extracted Output
    ocr_text: str
    ocr_regions: list[dict[str, Any]]
    ocr_confidence: float
    ocr_status: str  # AVAILABLE, UNAVAILABLE, SUCCESS, FAILED, SKIPPED

    # Object Detection Output
    detected_objects: list[dict[str, Any]]
    detection_confidence: float
    detection_status: str  # AVAILABLE, UNAVAILABLE, SUCCESS, FAILED, SKIPPED

    # Multimodal Vision Findings & Synthesis
    visual_findings: list[dict[str, Any]]
    analysis: dict[str, Any]
    answer: str

    # Evidence Grounding & Confidence
    confidence: float
    citations: list[dict[str, Any]]

    # Operational Lifecycle & Telemetry
    status: (
        str  # INITIALIZED, PREPROCESSED, ANALYZED, COMPLETED, FAILED_VALIDATION, FAILED
    )
    error: str | None
    warnings: list[str]
    execution_time_ms: float
