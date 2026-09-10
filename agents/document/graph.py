from typing import Any

from agents.document.nodes import (
    classify_document_node,
    extract_text_node,
    normalize_content_node,
    understand_document_node,
    validate_document_node,
    validate_result_node,
)
from agents.document.providers import BaseDocumentLLMProvider
from agents.document.state import DocumentState

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:
    StateGraph = None
    START = "__start__"
    END = "__end__"


def route_after_validation(state: DocumentState) -> str:
    """Routes to extraction or immediately to validate_result on validation failure."""
    if state.get("status") == "FAILED_VALIDATION":
        return "validate_result"
    return "extract_text"


def route_after_extraction(state: DocumentState) -> str:
    """Routes to normalization or immediately to validate_result on extraction failure."""
    if state.get("status") == "FAILED_EXTRACTION":
        return "validate_result"
    return "normalize_content"


def build_document_graph(provider: BaseDocumentLLMProvider | None = None):
    """
    Constructs and compiles the atomic LangGraph workflow for the Document Agent:
    START -> validate_document -> extract_text -> normalize_content
          -> classify_document -> understand_document -> validate_result -> END
    """
    if StateGraph is None:
        return None

    async def _understand_document(state: DocumentState) -> dict[str, Any]:
        return await understand_document_node(state, provider=provider)

    workflow = StateGraph(DocumentState)

    # Register individual atomic nodes
    workflow.add_node("validate_document", validate_document_node)
    workflow.add_node("extract_text", extract_text_node)
    workflow.add_node("normalize_content", normalize_content_node)
    workflow.add_node("classify_document", classify_document_node)
    workflow.add_node("understand_document", _understand_document)
    workflow.add_node("validate_result", validate_result_node)

    # Set Entry Point
    workflow.add_edge(START, "validate_document")

    # Conditional branch after validation
    workflow.add_conditional_edges(
        "validate_document",
        route_after_validation,
        {
            "extract_text": "extract_text",
            "validate_result": "validate_result"
        }
    )

    # Conditional branch after extraction
    workflow.add_conditional_edges(
        "extract_text",
        route_after_extraction,
        {
            "normalize_content": "normalize_content",
            "validate_result": "validate_result"
        }
    )

    # Sequential progression
    workflow.add_edge("normalize_content", "classify_document")
    workflow.add_edge("classify_document", "understand_document")
    workflow.add_edge("understand_document", "validate_result")
    workflow.add_edge("validate_result", END)

    return workflow.compile()
