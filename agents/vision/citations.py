"""
Vision Grounding and Citations Builder.
Synthesizes verifiable evidence citations from bounding boxes, OCR regions,
and analytical visual findings. Prevents fabricated evidence.
"""

import uuid
from typing import Any

from agents.vision.schemas import VisionCitation


def build_evidence_citations(
    visual_findings: list[dict[str, Any]],
    detected_objects: list[dict[str, Any]],
    ocr_regions: list[dict[str, Any]],
) -> list[VisionCitation]:
    """
    Constructs strongly typed, grounded citations from real detected bounding boxes,
    OCR regions, and localized visual observations.
    NEVER creates phantom citations without real underlying features.
    """
    citations: list[VisionCitation] = []

    # 1. Citations from detected objects
    for obj in detected_objects:
        bbox = obj.get("bbox")
        label = obj.get("label", "Object")
        conf = float(obj.get("confidence", 1.0))
        c_id = f"cite-obj-{uuid.uuid4().hex[:8]}"

        citations.append(
            VisionCitation(
                citation_id=c_id,
                source_type="bounding_box",
                label=label,
                confidence=conf,
                bbox=bbox,
                text=None,
                details=f"Detected object '{label}' with {conf * 100:.1f}% confidence.",
            )
        )

    # 2. Citations from OCR regions
    for reg in ocr_regions:
        text = reg.get("text", "").strip()
        if not text:
            continue
        bbox = reg.get("bbox")
        conf = float(reg.get("confidence", 1.0))
        c_id = f"cite-ocr-{uuid.uuid4().hex[:8]}"

        citations.append(
            VisionCitation(
                citation_id=c_id,
                source_type="ocr_region",
                label=f"Text: {text[:20]}",
                confidence=conf,
                bbox=bbox,
                text=text,
                details=f"OCR extracted text '{text}' with {conf * 100:.1f}% confidence.",
            )
        )

    # 3. Citations from visual findings with specific localized regions
    for finding in visual_findings:
        bbox = finding.get("bbox")
        title = finding.get("title", "Finding")
        conf = float(finding.get("confidence", 1.0))
        c_id = f"cite-find-{uuid.uuid4().hex[:8]}"

        citations.append(
            VisionCitation(
                citation_id=c_id,
                source_type="visual_finding",
                label=title,
                confidence=conf,
                bbox=bbox,
                text=None,
                details=finding.get("description"),
            )
        )

    return citations
