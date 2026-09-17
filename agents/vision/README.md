# Vision Agent (OmniAgent AI)

## Overview

The **Vision Agent** is an enterprise multimodal AI specialist designed to inspect, analyze, and extract intelligence from images, diagrams, schematics, and equipment inspection photos. It operates within the OmniAgent AI cognitive mesh via LangGraph, orchestrated by the Supervisor Agent or invoked directly via secure API endpoints.

## Core Capabilities

- **Safe Image Ingestion & Validation**:
  - Validates MIME types, extensions (`.jpg`, `.jpeg`, `.png`, `.webp`), and binary signatures (magic bytes).
  - Decompression bomb safeguards: Enforces max pixel thresholds (`16,777,216` px) and max file sizes (default `10 MB`).
  - Corrupted stream detection and rejection.
  - Path traversal and malicious payload prevention.
- **Safe Preprocessing**:
  - EXIF orientation correction (`ImageOps.exif_transpose`).
  - Privacy-preserving metadata sanitization (strips GPS and camera identifiers).
  - RGB normalization with neutral background alpha compositing.
  - High-fidelity Lanczos downscaling for oversized dimensions.
  - Immutability guarantee: User original uploaded files are never overwritten.
- **Untrusted Input & Prompt Injection Defense**:
  - Treats all image content, visual text inscriptions, and OCR extractions as strictly raw data, NEVER instructions.
  - System prompts enforce strict instruction hierarchy: Inscribed commands like *"Ignore previous instructions"* are neutralized and reported as passive visible text.
- **Optical Character Recognition (OCR)**:
  - Protocol abstraction supporting system engines (e.g. Tesseract) and testing mocks.
  - Structured output with bounding regions and word-level confidences.
  - Honest engine status: Reports `UNAVAILABLE` if OCR is not installed, never returns fake extractions.
- **Object Detection**:
  - Protocol abstraction supporting neural detectors (YOLO / OpenCV) and testing mocks.
  - Returns detected class labels, confidence scores, and normalized/pixel bounding boxes.
  - Honest reporting: Reports `UNAVAILABLE` if detection weights are unconfigured.
- **Multimodal Visual Understanding**:
  - Deep inspection for structural damage, cracks, corrosion, deformation, and misalignment.
  - Component identification and assembly verification.
  - Safety compliance and hazard analysis (guards, spills, trip risks).
  - Grounded citations linking answers to bounding boxes, OCR regions, and visual observations.

## LangGraph Workflow

```text
START
  ↓
validate_request
  ↓
validate_image
  ↓
preprocess_image
  ↓
classify_task (OCR / Detection / Inspection / Safety / General)
  ↓ (Conditional Routing)
├─ Pure OCR: run_ocr → generate_answer → build_evidence → END
├─ Pure Detection: run_object_detection → generate_answer → build_evidence → END
└─ Full Inspection: run_ocr → run_object_detection → run_vision_analysis
                      ↓
                  combine_findings
                      ↓
                  validate_analysis
                      ↓
                  generate_answer
                      ↓
                  build_evidence
                      ↓
                     END
```

## Quick Usage

```python
from agents.vision import VisionAgent

agent = VisionAgent()

result = await agent.analyze(
    image_id="img-uuid-12345",
    question="Are there any visible damaged components?",
    image_bytes=image_bytes,
    filename="machine_inspection.jpg",
    task_type="VISUAL_INSPECTION",
)

print(result.answer)
print(f"Confidence: {result.confidence}")
for finding in result.findings:
    print(f"- {finding.title} [{finding.severity}]: {finding.description}")
```
