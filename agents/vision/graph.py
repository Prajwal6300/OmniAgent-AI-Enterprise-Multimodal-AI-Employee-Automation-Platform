"""
Vision Agent LangGraph Workflow.
Defines the StateGraph topology, conditional branch routers,
and performance-optimized execution paths for OCR-only, detection-only, and deep multimodal inspection.
"""

from typing import Any

from agents.vision.analyzer import VisionProvider
from agents.vision.detector import ObjectDetector
from agents.vision.nodes import (
    build_evidence_node,
    classify_task_node,
    combine_findings_node,
    generate_answer_node,
    preprocess_image_node,
    run_object_detection_node,
    run_ocr_node,
    run_vision_analysis_node,
    validate_analysis_node,
    validate_image_node,
    validate_request_node,
)
from agents.vision.ocr import OCRProvider
from agents.vision.schemas import TaskType
from agents.vision.state import VisionState

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:
    StateGraph = None
    START = "__start__"
    END = "__end__"


def route_after_validation(state: VisionState) -> str:
    """Branches early to answer generation if validation fails."""
    if state.get("status") == "FAILED_VALIDATION":
        return "generate_answer"
    return "next"


def route_by_task_type(state: VisionState) -> str:
    """
    Performance-optimized conditional routing:
    - Pure OCR / text tasks bypass heavyweight object detection models.
    - Pure Object Detection tasks bypass OCR engine.
    - Deep inspection, damage analysis, and safety run coordinated multi-modal processors.
    - General analysis routes directly to vision understanding model.
    """
    if state.get("status") == "FAILED_VALIDATION":
        return "build_evidence"

    task = state.get("task_type", TaskType.GENERAL_IMAGE_ANALYSIS.value)

    if task in (TaskType.OCR.value, TaskType.TEXT_EXTRACTION.value):
        return "run_ocr"

    if task == TaskType.OBJECT_DETECTION.value:
        return "run_object_detection"

    if task in (
        TaskType.VISUAL_INSPECTION.value,
        TaskType.DAMAGE_ANALYSIS.value,
        TaskType.COMPONENT_IDENTIFICATION.value,
        TaskType.SAFETY_ANALYSIS.value,
        TaskType.DOCUMENT_IMAGE_ANALYSIS.value,
    ):
        return "run_ocr"  # Start full pipeline: OCR -> Detector -> Vision Model

    return "run_vision_analysis"


def build_vision_graph(
    vision_provider: VisionProvider | None = None,
    ocr_provider: OCRProvider | None = None,
    detector: ObjectDetector | None = None,
):
    """
    Constructs and compiles the atomic LangGraph workflow for the Vision Agent.
    """
    if StateGraph is None:
        return None

    # Custom node wrappers to bind injected providers if present
    async def _run_ocr(state: VisionState) -> dict[str, Any]:
        return await run_ocr_node(state, ocr_provider=ocr_provider)

    async def _run_detector(state: VisionState) -> dict[str, Any]:
        return await run_object_detection_node(state, detector=detector)

    async def _run_vision(state: VisionState) -> dict[str, Any]:
        return await run_vision_analysis_node(state, vision_provider=vision_provider)

    workflow = StateGraph(VisionState)

    # 1. Register atomic nodes
    workflow.add_node("validate_request", validate_request_node)
    workflow.add_node("validate_image", validate_image_node)
    workflow.add_node("preprocess_image", preprocess_image_node)
    workflow.add_node("classify_task", classify_task_node)

    workflow.add_node("run_ocr", _run_ocr)
    workflow.add_node("run_object_detection", _run_detector)
    workflow.add_node("run_vision_analysis", _run_vision)

    workflow.add_node("combine_findings", combine_findings_node)
    workflow.add_node("validate_analysis", validate_analysis_node)
    workflow.add_node("generate_answer", generate_answer_node)
    workflow.add_node("build_evidence", build_evidence_node)

    # 2. Wire edges with conditional shortcuts
    workflow.add_edge(START, "validate_request")

    # After request validation
    workflow.add_conditional_edges(
        "validate_request",
        route_after_validation,
        {"next": "validate_image", "generate_answer": "generate_answer"},
    )

    # After image validation
    workflow.add_conditional_edges(
        "validate_image",
        route_after_validation,
        {"next": "preprocess_image", "generate_answer": "generate_answer"},
    )

    # After image preprocessing
    workflow.add_conditional_edges(
        "preprocess_image",
        route_after_validation,
        {"next": "classify_task", "generate_answer": "generate_answer"},
    )

    # Dynamic dispatch after task classification
    workflow.add_conditional_edges(
        "classify_task",
        route_by_task_type,
        {
            "run_ocr": "run_ocr",
            "run_object_detection": "run_object_detection",
            "run_vision_analysis": "run_vision_analysis",
            "build_evidence": "build_evidence",
        },
    )

    # Conditional progression from OCR
    def route_after_ocr(state: VisionState) -> str:
        task = state.get("task_type")
        if task in (TaskType.OCR.value, TaskType.TEXT_EXTRACTION.value):
            return "generate_answer"
        return "run_object_detection"

    workflow.add_conditional_edges(
        "run_ocr",
        route_after_ocr,
        {
            "generate_answer": "generate_answer",
            "run_object_detection": "run_object_detection",
        },
    )

    # Conditional progression from Object Detection
    def route_after_detector(state: VisionState) -> str:
        task = state.get("task_type")
        if task == TaskType.OBJECT_DETECTION.value:
            return "generate_answer"
        return "run_vision_analysis"

    workflow.add_conditional_edges(
        "run_object_detection",
        route_after_detector,
        {
            "generate_answer": "generate_answer",
            "run_vision_analysis": "run_vision_analysis",
        },
    )

    # Standard pipeline completion
    workflow.add_edge("run_vision_analysis", "combine_findings")
    workflow.add_edge("combine_findings", "validate_analysis")
    workflow.add_edge("validate_analysis", "generate_answer")
    workflow.add_edge("generate_answer", "build_evidence")
    workflow.add_edge("build_evidence", END)

    return workflow.compile()


async def run_sequential_flow(
    state: VisionState,
    vision_provider: VisionProvider | None = None,
    ocr_provider: OCRProvider | None = None,
    detector: ObjectDetector | None = None,
) -> VisionState:
    """
    Sequential execution fallback if StateGraph is not available.
    Adheres strictly to the identical conditional routing semantics.
    """
    current_state = dict(state)

    # 1. validate_request
    res = await validate_request_node(current_state)
    current_state.update(res)
    if current_state.get("status") == "FAILED_VALIDATION":
        ans = await generate_answer_node(current_state)
        current_state.update(ans)
        ev = await build_evidence_node(current_state)
        current_state.update(ev)
        return current_state

    # 2. validate_image
    res = await validate_image_node(current_state)
    current_state.update(res)
    if current_state.get("status") == "FAILED_VALIDATION":
        ans = await generate_answer_node(current_state)
        current_state.update(ans)
        ev = await build_evidence_node(current_state)
        current_state.update(ev)
        return current_state

    # 3. preprocess_image
    res = await preprocess_image_node(current_state)
    current_state.update(res)
    if current_state.get("status") == "FAILED_VALIDATION":
        ans = await generate_answer_node(current_state)
        current_state.update(ans)
        ev = await build_evidence_node(current_state)
        current_state.update(ev)
        return current_state

    # 4. classify_task
    res = await classify_task_node(current_state)
    current_state.update(res)

    task = current_state.get("task_type", TaskType.GENERAL_IMAGE_ANALYSIS.value)

    # 5. Targeted execution branches
    if task in (TaskType.OCR.value, TaskType.TEXT_EXTRACTION.value):
        res = await run_ocr_node(current_state, ocr_provider=ocr_provider)
        current_state.update(res)
    elif task == TaskType.OBJECT_DETECTION.value:
        res = await run_object_detection_node(current_state, detector=detector)
        current_state.update(res)
    elif task in (
        TaskType.VISUAL_INSPECTION.value,
        TaskType.DAMAGE_ANALYSIS.value,
        TaskType.COMPONENT_IDENTIFICATION.value,
        TaskType.SAFETY_ANALYSIS.value,
        TaskType.DOCUMENT_IMAGE_ANALYSIS.value,
    ):
        res_ocr = await run_ocr_node(current_state, ocr_provider=ocr_provider)
        current_state.update(res_ocr)
        res_det = await run_object_detection_node(current_state, detector=detector)
        current_state.update(res_det)
        res_vis = await run_vision_analysis_node(
            current_state, vision_provider=vision_provider
        )
        current_state.update(res_vis)
        res_comb = await combine_findings_node(current_state)
        current_state.update(res_comb)
        res_val = await validate_analysis_node(current_state)
        current_state.update(res_val)
    else:
        # General analysis
        res_vis = await run_vision_analysis_node(
            current_state, vision_provider=vision_provider
        )
        current_state.update(res_vis)
        res_comb = await combine_findings_node(current_state)
        current_state.update(res_comb)
        res_val = await validate_analysis_node(current_state)
        current_state.update(res_val)

    # 6. Answer synthesis & Evidence citations
    res_ans = await generate_answer_node(current_state)
    current_state.update(res_ans)
    res_ev = await build_evidence_node(current_state)
    current_state.update(res_ev)

    return current_state
