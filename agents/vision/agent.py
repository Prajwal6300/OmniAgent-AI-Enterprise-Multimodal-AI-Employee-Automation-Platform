"""
Vision Agent Main Interface.
Orchestrates enterprise visual inspection, OCR, and object detection workflows
through LangGraph, enforcing tenant isolation, latency tracking, and structured audit telemetry.
"""

import time
import uuid
from typing import Any

try:
    from app.core.logging import logger
except ImportError:
    try:
        from backend.app.core.logging import logger
    except ImportError:
        import logging

        logger = logging.getLogger("omniagent.vision.agent")

from agents.vision.analyzer import VisionProvider, get_vision_provider
from agents.vision.detector import ObjectDetector, get_object_detector
from agents.vision.graph import build_vision_graph, run_sequential_flow
from agents.vision.ocr import OCRProvider, get_ocr_provider
from agents.vision.schemas import (
    ComponentStatuses,
    ImageMetadata,
    OCRRegion,
    OCRResult,
    ProcessorStatus,
    TaskType,
    VisionAnalysisResult,
    VisionCitation,
    VisionDetection,
    VisualFinding,
)
from agents.vision.state import VisionState


class VisionAgent:
    """
    OmniAgent Vision Specialist: Enterprise Multimodal AI Employee.
    Analyzes visual images, engineering schematics, machine inspections,
    extracts textual inscriptions via OCR, and detects physical objects/components.
    """

    def __init__(
        self,
        vision_provider: VisionProvider | None = None,
        ocr_provider: OCRProvider | None = None,
        detector: ObjectDetector | None = None,
    ):
        self.vision_provider = vision_provider or get_vision_provider()
        self.ocr_provider = ocr_provider or get_ocr_provider()
        self.detector = detector or get_object_detector()

        self._compiled_graph = build_vision_graph(
            vision_provider=self.vision_provider,
            ocr_provider=self.ocr_provider,
            detector=self.detector,
        )

    async def analyze(
        self,
        image_id: str,
        question: str,
        image_bytes: bytes | None = None,
        image_path: str | None = None,
        filename: str = "image.jpg",
        mime_type: str | None = None,
        task_type: str | None = None,
        user_id: str | None = None,
        organization_id: str | None = None,
        conversation_id: str | None = None,
        request_id: str | None = None,
    ) -> VisionAnalysisResult:
        """
        Main entrypoint for visual intelligence operations.
        Executes LangGraph pipeline with strict safety, citation tracking, and partial-failure handling.
        """
        start_time = time.time()
        req_id = request_id or str(uuid.uuid4())
        u_id = user_id or "anonymous"
        org_id = organization_id or "default_org"
        conv_id = conversation_id or str(uuid.uuid4())

        initial_state: VisionState = {
            "request_id": req_id,
            "user_id": u_id,
            "organization_id": org_id,
            "conversation_id": conv_id,
            "image_id": str(image_id),
            "filename": filename,
            "mime_type": mime_type or "",
            "image_bytes": image_bytes,
            "image_path": image_path or "",
            "preprocessed_image_path": "",
            "image_width": 0,
            "image_height": 0,
            "image_format": "JPEG",
            "image_size_bytes": len(image_bytes) if image_bytes else 0,
            "question": question,
            "task_type": task_type or "",
            "ocr_text": "",
            "ocr_regions": [],
            "ocr_confidence": 0.0,
            "ocr_status": ProcessorStatus.UNAVAILABLE.value,
            "detected_objects": [],
            "detection_confidence": 0.0,
            "detection_status": ProcessorStatus.UNAVAILABLE.value,
            "visual_findings": [],
            "analysis": {},
            "answer": "",
            "confidence": 1.0,
            "citations": [],
            "status": "INITIALIZED",
            "error": None,
            "warnings": [],
        }

        try:
            if self._compiled_graph is not None:
                final_state = await self._compiled_graph.ainvoke(initial_state)
            else:
                final_state = await run_sequential_flow(
                    initial_state,
                    vision_provider=self.vision_provider,
                    ocr_provider=self.ocr_provider,
                    detector=self.detector,
                )

            latency_ms = round((time.time() - start_time) * 1000, 2)

            # Build strongly typed Pydantic result
            findings_data = [
                VisualFinding(**f) for f in final_state.get("visual_findings", [])
            ]
            detections_data = [
                VisionDetection(**d) for d in final_state.get("detected_objects", [])
            ]
            ocr_regions_data = [
                OCRRegion(**r) for r in final_state.get("ocr_regions", [])
            ]
            ocr_result = OCRResult(
                text=final_state.get("ocr_text", ""),
                confidence=final_state.get("ocr_confidence", 0.0),
                status=final_state.get("ocr_status", ProcessorStatus.UNAVAILABLE.value),
                regions=ocr_regions_data,
            )
            citations_data = [
                VisionCitation(**c) for c in final_state.get("citations", [])
            ]
            img_meta = ImageMetadata(
                width=final_state.get("image_width", 0),
                height=final_state.get("image_height", 0),
                format=final_state.get("image_format", "JPEG"),
                size_bytes=final_state.get("image_size_bytes", 0),
            )

            vision_status = (
                ProcessorStatus.SUCCESS.value
                if final_state.get("status") == "COMPLETED"
                else ProcessorStatus.FAILED.value
            )
            comp_statuses = ComponentStatuses(
                vision_model=vision_status,
                ocr=final_state.get("ocr_status", ProcessorStatus.UNAVAILABLE.value),
                object_detection=final_state.get(
                    "detection_status", ProcessorStatus.UNAVAILABLE.value
                ),
            )

            result = VisionAnalysisResult(
                request_id=req_id,
                image_id=str(image_id),
                task_type=final_state.get(
                    "task_type", TaskType.GENERAL_IMAGE_ANALYSIS.value
                ),
                question=question,
                summary=final_state.get("analysis", {}).get(
                    "summary", "Image analysis completed."
                ),
                answer=final_state.get("answer", "Analysis finished."),
                findings=findings_data,
                detected_objects=detections_data,
                ocr_result=ocr_result,
                citations=citations_data,
                confidence=final_state.get("confidence", 1.0),
                image_metadata=img_meta,
                component_statuses=comp_statuses,
                warnings=final_state.get("warnings", []),
                execution_time_ms=latency_ms,
            )

            logger.info(
                "vision_analysis_completed",
                request_id=req_id,
                image_id=str(image_id),
                task_type=result.task_type,
                latency_ms=latency_ms,
                findings_count=len(result.findings),
                detections_count=len(result.detected_objects),
                citations_count=len(result.citations),
                confidence=result.confidence,
            )

            return result

        except Exception as exc:  # noqa: BLE001
            latency_ms = round((time.time() - start_time) * 1000, 2)
            logger.error("vision_agent_failed", request_id=req_id, error=str(exc))
            return VisionAnalysisResult(
                request_id=req_id,
                image_id=str(image_id),
                task_type=task_type or TaskType.UNKNOWN.value,
                question=question,
                summary="Vision processing encountered an unrecoverable failure.",
                answer=f"Vision Agent execution error: {exc!s}",
                findings=[],
                detected_objects=[],
                ocr_result=OCRResult(
                    status=ProcessorStatus.FAILED.value, error=str(exc)
                ),
                citations=[],
                confidence=0.0,
                image_metadata=ImageMetadata(),
                component_statuses=ComponentStatuses(
                    vision_model=ProcessorStatus.FAILED.value,
                    ocr=ProcessorStatus.FAILED.value,
                    object_detection=ProcessorStatus.FAILED.value,
                ),
                warnings=[f"Execution failed: {exc!s}"],
                execution_time_ms=latency_ms,
            )

    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Backward-compatibility interface for legacy invocation."""
        image_id = state.get("image_id", str(uuid.uuid4()))
        question = (
            state.get("question")
            or state.get("task_description")
            or "Analyze visible image features."
        )
        res = await self.analyze(
            image_id=image_id,
            question=question,
            image_bytes=state.get("image_bytes"),
            image_path=state.get("image_path"),
            task_type=state.get("task_type"),
        )
        return {
            "status": "success" if res.confidence > 0.0 else "failed",
            "agent": "vision",
            "result": res.model_dump(),
        }
