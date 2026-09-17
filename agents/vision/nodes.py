"""
Atomic LangGraph Nodes for Vision Agent.
Implements each discrete processing stage in the computer vision pipeline
with robust error handling, partial failure resilience, and prompt injection defense.
"""

import os
from typing import Any

try:
    from app.core.config import settings
except ImportError:
    try:
        from backend.app.core.config import settings
    except ImportError:

        class SettingsFallback:
            VISION_MAX_FILE_SIZE_MB = 10
            VISION_MAX_WIDTH = 4096
            VISION_MAX_HEIGHT = 4096
            VISION_MAX_IMAGE_PIXELS = 16_777_216
            VISION_OCR_ENABLED = True
            VISION_OBJECT_DETECTION_ENABLED = True
            VISION_PROVIDER = "mock"
            VISION_MODEL = "gpt-4o"

        settings = SettingsFallback()

try:
    from app.core.logging import logger
except ImportError:
    try:
        from backend.app.core.logging import logger
    except ImportError:
        import logging

        logger = logging.getLogger("omniagent.vision.nodes")

from agents.vision.analyzer import VisionProvider, get_vision_provider
from agents.vision.citations import build_evidence_citations
from agents.vision.detector import ObjectDetector, get_object_detector
from agents.vision.exceptions import (
    VisionProcessingError,
    VisionSecurityError,
    VisionValidationError,
)
from agents.vision.ocr import OCRProvider, get_ocr_provider
from agents.vision.preprocessing import preprocess_image, validate_image_metadata
from agents.vision.schemas import ProcessorStatus, TaskType
from agents.vision.security import (
    detect_prompt_injection,
    sanitize_filename_safely,
)
from agents.vision.state import VisionState


async def validate_request_node(state: VisionState) -> dict[str, Any]:
    """
    Validates the incoming vision analysis request.
    Verifies query existence, prompt injection patterns, and image payload presence.
    """
    question = (state.get("question") or "").strip()
    if not question:
        return {
            "status": "FAILED_VALIDATION",
            "error": "Question or visual inquiry prompt cannot be empty.",
            "confidence": 0.0,
        }

    # Prompt injection detection on user question
    is_inj, pattern = detect_prompt_injection(question)
    warnings = list(state.get("warnings") or [])
    if is_inj:
        warnings.append(
            f"Adversarial prompt pattern detected in question: '{pattern}'. Query will be evaluated under strict security boundaries."
        )

    has_bytes = bool(state.get("image_bytes"))
    has_path = bool(state.get("image_path") and os.path.exists(state["image_path"]))

    if not has_bytes and not has_path:
        return {
            "status": "FAILED_VALIDATION",
            "error": "No image payload provided (image_bytes or accessible image_path required).",
            "confidence": 0.0,
            "warnings": warnings,
        }

    return {"question": question, "warnings": warnings, "status": "INITIALIZED"}


async def validate_image_node(state: VisionState) -> dict[str, Any]:
    """
    Validates image binary headers, file size, extensions, and MIME types.
    Protects against disguised executables and corrupt streams.
    """
    if state.get("status") == "FAILED_VALIDATION":
        return {}

    image_bytes = state.get("image_bytes")
    image_path = state.get("image_path")
    filename = state.get("filename") or "image.jpg"
    mime_type = state.get("mime_type")

    # Load bytes if only path was provided
    if not image_bytes and image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as f:  # noqa: ASYNC230
                image_bytes = f.read()
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "FAILED_VALIDATION",
                "error": f"Failed to read image from path '{image_path}': {exc!s}",
                "confidence": 0.0,
            }

    try:
        canonical_format = validate_image_metadata(
            filename=filename, file_bytes=image_bytes, mime_type=mime_type
        )
        return {
            "image_bytes": image_bytes,
            "image_format": canonical_format,
            "image_size_bytes": len(image_bytes),
            "filename": sanitize_filename_safely(filename),
        }
    except (VisionValidationError, VisionSecurityError) as exc:
        return {"status": "FAILED_VALIDATION", "error": exc.message, "confidence": 0.0}
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "FAILED_VALIDATION",
            "error": f"Image validation failed: {exc!s}",
            "confidence": 0.0,
        }


async def preprocess_image_node(state: VisionState) -> dict[str, Any]:
    """
    Normalizes image: EXIF orientation correction, RGB conversion,
    decompression bomb checks, and optional resizing.
    """
    if state.get("status") == "FAILED_VALIDATION":
        return {}

    image_bytes = state.get("image_bytes")
    filename = state.get("filename") or "image.jpg"
    mime_type = state.get("mime_type")

    try:
        clean_bytes, meta = preprocess_image(
            file_bytes=image_bytes, filename=filename, mime_type=mime_type
        )
        return {
            "image_bytes": clean_bytes,
            "image_width": meta["width"],
            "image_height": meta["height"],
            "image_format": meta["format"],
            "image_size_bytes": meta["preprocessed_size_bytes"],
            "status": "PREPROCESSED",
        }
    except (VisionValidationError, VisionProcessingError) as exc:
        return {"status": "FAILED_VALIDATION", "error": exc.message, "confidence": 0.0}
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "FAILED_VALIDATION",
            "error": f"Image preprocessing failed: {exc!s}",
            "confidence": 0.0,
        }


def classify_task_heuristically(question: str) -> str:
    """
    Deterministic rule-based task classifier for immediate, offline classification.
    """
    q = question.strip().lower()

    # 1. OCR / Text Extraction
    if any(
        k in q
        for k in [
            "serial number",
            "extract text",
            "read text",
            "read the text",
            "ocr",
            "what text",
            "transcribe",
            "text visible",
            "read the serial",
            "words in this",
            "inscription",
            "license plate",
            "barcode",
            "qr code",
        ]
    ):
        if "serial" in q or "extract" in q:
            return TaskType.TEXT_EXTRACTION.value
        return TaskType.OCR.value

    # 2. Visual Inspection
    if any(
        k in q
        for k in [
            "inspect",
            "inspection",
            "machine inspection",
            "condition check",
            "audit this machine",
            "examine",
            "compare the visible condition",
        ]
    ):
        return TaskType.VISUAL_INSPECTION.value

    # 3. Damage Analysis
    if any(
        k in q
        for k in [
            "damage",
            "damaged",
            "crack",
            "corrosion",
            "dent",
            "fracture",
            "leak",
            "scratched",
            "broken",
            "deformation",
            "wear and tear",
            "wear",
            "rust",
            "fault",
            "defect",
        ]
    ):
        return TaskType.DAMAGE_ANALYSIS.value

    # 4. Component Identification
    if any(
        k in q
        for k in [
            "component",
            "components",
            "part",
            "parts",
            "assemblies",
            "what components",
            "identify components",
            "hardware parts",
            "connectors",
            "fittings",
        ]
    ):
        return TaskType.COMPONENT_IDENTIFICATION.value

    # 5. Safety Analysis
    if any(
        k in q
        for k in [
            "safety",
            "hazard",
            "ppe",
            "protective equipment",
            "danger",
            "safety guard",
            "violation",
            "spill",
            "trip hazard",
        ]
    ):
        return TaskType.SAFETY_ANALYSIS.value

    # 6. Object Detection
    if any(
        k in q
        for k in [
            "detect objects",
            "bounding box",
            "locate objects",
            "object detection",
            "detect all",
            "count objects",
            "where is the",
        ]
    ):
        return TaskType.OBJECT_DETECTION.value

    # 7. Document Image Analysis
    if any(
        k in q
        for k in [
            "document image",
            "scanned document",
            "form",
            "invoice image",
            "receipt image",
        ]
    ):
        return TaskType.DOCUMENT_IMAGE_ANALYSIS.value

    # 8. Image Classification
    if any(
        k in q
        for k in [
            "classify this image",
            "image category",
            "what kind of image",
            "classify image",
        ]
    ):
        return TaskType.IMAGE_CLASSIFICATION.value

    return TaskType.GENERAL_IMAGE_ANALYSIS.value


async def classify_task_node(state: VisionState) -> dict[str, Any]:
    """
    Classifies the user prompt into structured TaskType categories.
    Preserves explicitly specified task_type if provided and valid.
    """
    if state.get("status") == "FAILED_VALIDATION":
        return {}

    req_task = state.get("task_type")
    valid_tasks = {t.value for t in TaskType}

    if (
        req_task
        and req_task.upper() in valid_tasks
        and req_task.upper()
        not in (TaskType.UNKNOWN.value, TaskType.GENERAL_IMAGE_ANALYSIS.value, "")
    ):
        final_task = req_task.upper()
    else:
        final_task = classify_task_heuristically(state.get("question", ""))

    return {"task_type": final_task}


async def run_ocr_node(
    state: VisionState, ocr_provider: OCRProvider | None = None
) -> dict[str, Any]:
    """
    Executes OCR text extraction. Handles engine absence gracefully without fake results.
    Inspects extracted text for prompt injection.
    """
    if state.get("status") == "FAILED_VALIDATION":
        return {}

    provider = ocr_provider or get_ocr_provider()
    image_bytes = state.get("image_bytes")
    image_path = state.get("image_path")

    try:
        res = await provider.extract_text(
            image_path=image_path, image_bytes=image_bytes
        )
        text = res.get("text", "")
        conf = float(res.get("confidence", 0.0))
        status = res.get("status", ProcessorStatus.SUCCESS.value)
        regions = res.get("regions", [])

        warnings = list(state.get("warnings") or [])
        if res.get("message"):
            warnings.append(f"OCR Notice: {res['message']}")

        # Security check on extracted OCR text
        if text:
            is_inj, pattern = detect_prompt_injection(text)
            if is_inj:
                warnings.append(
                    f"Untrusted image text contains adversarial prompt pattern: '{pattern}'. "
                    "Treated as raw data only; system directives remain enforced."
                )

        return {
            "ocr_text": text,
            "ocr_regions": regions,
            "ocr_confidence": conf,
            "ocr_status": status,
            "warnings": warnings,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("ocr_node_exception", error=str(exc))
        warnings = list(state.get("warnings") or [])
        warnings.append(f"OCR extraction failed: {exc!s}")
        return {
            "ocr_text": "",
            "ocr_regions": [],
            "ocr_confidence": 0.0,
            "ocr_status": ProcessorStatus.FAILED.value,
            "warnings": warnings,
        }


async def run_object_detection_node(
    state: VisionState, detector: ObjectDetector | None = None
) -> dict[str, Any]:
    """
    Executes object detection. Honestly reports model availability.
    """
    if state.get("status") == "FAILED_VALIDATION":
        return {}

    det = detector or get_object_detector()
    image_bytes = state.get("image_bytes")
    image_path = state.get("image_path")

    try:
        detections, status, msg = await det.detect(
            image_path=image_path, image_bytes=image_bytes
        )
        warnings = list(state.get("warnings") or [])
        if msg:
            warnings.append(f"Detector Notice: {msg}")

        avg_conf = (
            sum(float(d.get("confidence", 0.0)) for d in detections) / len(detections)
            if detections
            else 0.0
        )

        return {
            "detected_objects": detections,
            "detection_confidence": round(avg_conf, 4),
            "detection_status": status,
            "warnings": warnings,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("detector_node_exception", error=str(exc))
        warnings = list(state.get("warnings") or [])
        warnings.append(f"Object detection failed: {exc!s}")
        return {
            "detected_objects": [],
            "detection_confidence": 0.0,
            "detection_status": ProcessorStatus.FAILED.value,
            "warnings": warnings,
        }


async def run_vision_analysis_node(
    state: VisionState, vision_provider: VisionProvider | None = None
) -> dict[str, Any]:
    """
    Executes high-level multimodal image understanding and visual reasoning.
    """
    if state.get("status") == "FAILED_VALIDATION":
        return {}

    provider = vision_provider or get_vision_provider()
    image_bytes = state.get("image_bytes")
    question = state.get("question", "")
    task_type = state.get("task_type", TaskType.GENERAL_IMAGE_ANALYSIS.value)

    ocr_data = {
        "text": state.get("ocr_text", ""),
        "confidence": state.get("ocr_confidence", 0.0),
        "status": state.get("ocr_status", ProcessorStatus.UNAVAILABLE.value),
        "regions": state.get("ocr_regions", []),
    }
    detections = state.get("detected_objects", [])

    try:
        analysis_res = await provider.analyze(
            image_bytes=image_bytes,
            question=question,
            task_type=task_type,
            ocr_result=ocr_data,
            detected_objects=detections,
        )

        findings = analysis_res.get("findings", [])
        warnings = list(state.get("warnings") or [])
        warnings.extend(analysis_res.get("warnings", []))

        return {
            "analysis": analysis_res,
            "visual_findings": findings,
            "answer": analysis_res.get("answer", ""),
            "confidence": float(analysis_res.get("confidence", 0.9)),
            "warnings": warnings,
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("vision_analysis_node_failed", error=str(exc))
        warnings = list(state.get("warnings") or [])
        warnings.append(f"Vision model analysis failed: {exc!s}")
        return {
            "analysis": {},
            "visual_findings": [],
            "answer": f"Unable to complete visual model analysis: {exc!s}",
            "confidence": 0.0,
            "warnings": warnings,
        }


async def combine_findings_node(state: VisionState) -> dict[str, Any]:
    """
    Correlates findings from OCR, object detection, and visual inspection.
    """
    if state.get("status") == "FAILED_VALIDATION":
        return {}

    findings = list(state.get("visual_findings") or [])

    # If OCR produced text and it wasn't already in findings, integrate it
    ocr_text = (state.get("ocr_text") or "").strip()
    if ocr_text and not any(f.get("category") == "text" for f in findings):
        findings.append(
            {
                "title": "Visible Inscription",
                "description": f"Verified text inscription detected in image: '{ocr_text}'.",
                "severity": "INFO",
                "confidence": state.get("ocr_confidence", 0.9),
                "bbox": state.get("ocr_regions", [{}])[0].get("bbox")
                if state.get("ocr_regions")
                else None,
                "category": "text",
            }
        )

    # If detected objects exist and are not represented in findings, integrate them
    detected = state.get("detected_objects") or []
    existing_labels = {f.get("title", "").lower() for f in findings}
    for obj in detected:
        lbl = obj.get("label", "component")
        if f"component: {lbl.lower()}" not in existing_labels:
            findings.append(
                {
                    "title": f"Component: {lbl}",
                    "description": f"Identified {lbl} with {obj.get('confidence', 0.9) * 100:.1f}% confidence.",
                    "severity": "INFO",
                    "confidence": obj.get("confidence", 0.9),
                    "bbox": obj.get("bbox"),
                    "category": "component",
                }
            )

    return {"visual_findings": findings}


async def validate_analysis_node(state: VisionState) -> dict[str, Any]:
    """
    Ensures findings integrity, clamps confidence scores, and verifies response quality.
    """
    if state.get("status") == "FAILED_VALIDATION":
        return {}

    conf = float(state.get("confidence", 0.9))
    clamped_conf = max(0.0, min(1.0, conf))

    # If OCR was required by the task and failed, or vision failed, adjust confidence
    task_type = state.get("task_type", "")
    if task_type in ("OCR", "TEXT_EXTRACTION") and state.get("ocr_status") in (
        ProcessorStatus.FAILED.value,
        ProcessorStatus.UNAVAILABLE.value,
    ):
        clamped_conf = min(clamped_conf, 0.4)

    return {"confidence": round(clamped_conf, 4)}


async def generate_answer_node(state: VisionState) -> dict[str, Any]:
    """
    Generates finalized, grounded answer if the vision provider did not already format one,
    or formats targeted responses for OCR-only and Detection-only workflows.
    """
    if state.get("status") == "FAILED_VALIDATION":
        return {
            "answer": f"Analysis failed: {state.get('error', 'Validation error occurred.')}",
            "confidence": 0.0,
        }

    existing_answer = state.get("answer")
    task_type = state.get("task_type", "")

    # For pure OCR queries, ensure clean verbatim text presentation
    if task_type in ("OCR", "TEXT_EXTRACTION") and not existing_answer:
        ocr_text = (state.get("ocr_text") or "").strip()
        ocr_status = state.get("ocr_status", "")
        if ocr_status == ProcessorStatus.UNAVAILABLE.value:
            answer = "OCR is not configured for this deployment. Unable to extract textual inscription."
        elif ocr_text:
            answer = f"Extracted Text:\n{ocr_text}"
        else:
            answer = "No legible text was detected in the provided image."
        return {"answer": answer}

    # For pure Object Detection queries, summarize detections
    if task_type == TaskType.OBJECT_DETECTION.value and not existing_answer:
        detections = state.get("detected_objects") or []
        det_status = state.get("detection_status", "")
        if det_status == ProcessorStatus.UNAVAILABLE.value:
            answer = "Object detection is not configured for this deployment."
        elif detections:
            classes = [
                f"{d['label']} ({d['confidence'] * 100:.1f}%)" for d in detections
            ]
            answer = f"Detected {len(detections)} object(s):\n• " + "\n• ".join(classes)
        else:
            answer = "No matching objects were detected in the image."
        return {"answer": answer}

    if not existing_answer:
        findings = state.get("visual_findings") or []
        summary_points = [
            f"• {f.get('title')}: {f.get('description')}" for f in findings
        ]
        answer = (
            "Visual inspection completed:\n" + "\n".join(summary_points)
            if summary_points
            else "Visual inspection completed."
        )
        return {"answer": answer}

    return {}


async def build_evidence_node(state: VisionState) -> dict[str, Any]:
    """
    Builds grounded citations from detected bounding boxes, OCR regions,
    and visual observations. Sets final status to COMPLETED.
    """
    if state.get("status") == "FAILED_VALIDATION":
        return {"citations": [], "status": "FAILED"}

    findings = state.get("visual_findings") or []
    objects = state.get("detected_objects") or []
    ocr_regions = state.get("ocr_regions") or []

    citations = build_evidence_citations(
        visual_findings=findings, detected_objects=objects, ocr_regions=ocr_regions
    )

    return {"citations": [c.model_dump() for c in citations], "status": "COMPLETED"}
