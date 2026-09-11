from typing import Any

from agents.rag.citations import CitationBuilder
from agents.rag.context import ContextBuilder
from agents.rag.embeddings import BaseEmbeddingProvider
from agents.rag.nodes import (
    build_citations_node,
    build_context_node,
    filter_context_node,
    generate_answer_node,
    generate_query_embedding_node,
    retrieve_chunks_node,
    validate_grounding_node,
    validate_query_node,
)
from agents.rag.providers import BaseRAGLLMProvider
from agents.rag.reranker import BaseReranker
from agents.rag.retriever import BaseRAGRetriever
from agents.rag.state import RAGState

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:
    StateGraph = None
    START = "__start__"
    END = "__end__"


def route_after_validation(state: RAGState) -> str:
    """Routes to embedding generation, or directly to citations on validation failure."""
    if state.get("status") == "FAILED_VALIDATION":
        return "build_citations"
    return "generate_query_embedding"


def route_after_retrieval(state: RAGState) -> str:
    """If no chunks found or retrieval failed, skip filtering and go directly to generate answer (for fallback refusal)."""
    if state.get("status") == "FAILED_RETRIEVAL" or not state.get("retrieved_chunks"):
        return "generate_answer"
    return "filter_context"


def build_rag_graph(
    provider: BaseRAGLLMProvider | None = None,
    embedding_provider: BaseEmbeddingProvider | None = None,
    retriever: BaseRAGRetriever | None = None,
    reranker: BaseReranker | None = None,
    context_builder: ContextBuilder | None = None,
    citation_builder: CitationBuilder | None = None,
):
    """
    Constructs and compiles the atomic LangGraph workflow for the RAG Agent:
    START -> validate_query -> generate_query_embedding -> retrieve_chunks
          -> filter_context -> build_context -> generate_answer
          -> validate_grounding -> build_citations -> END
    """
    if StateGraph is None:
        return None

    async def _generate_query_embedding(state: RAGState) -> dict[str, Any]:
        return await generate_query_embedding_node(state, provider=embedding_provider)

    async def _retrieve_chunks(state: RAGState) -> dict[str, Any]:
        return await retrieve_chunks_node(state, retriever=retriever)

    async def _filter_context(state: RAGState) -> dict[str, Any]:
        return await filter_context_node(state, reranker=reranker)

    async def _build_context(state: RAGState) -> dict[str, Any]:
        return await build_context_node(state, builder=context_builder)

    async def _generate_answer(state: RAGState) -> dict[str, Any]:
        return await generate_answer_node(state, provider=provider)

    async def _build_citations(state: RAGState) -> dict[str, Any]:
        return await build_citations_node(state, builder=citation_builder)

    workflow = StateGraph(RAGState)

    # Register individual atomic nodes
    workflow.add_node("validate_query", validate_query_node)
    workflow.add_node("generate_query_embedding", _generate_query_embedding)
    workflow.add_node("retrieve_chunks", _retrieve_chunks)
    workflow.add_node("filter_context", _filter_context)
    workflow.add_node("build_context", _build_context)
    workflow.add_node("generate_answer", _generate_answer)
    workflow.add_node("validate_grounding", validate_grounding_node)
    workflow.add_node("build_citations", _build_citations)

    # Set Entry Point
    workflow.add_edge(START, "validate_query")

    # Conditional branch after validation
    workflow.add_conditional_edges(
        "validate_query",
        route_after_validation,
        {
            "generate_query_embedding": "generate_query_embedding",
            "build_citations": "build_citations"
        }
    )

    workflow.add_edge("generate_query_embedding", "retrieve_chunks")

    # Conditional branch after retrieval
    workflow.add_conditional_edges(
        "retrieve_chunks",
        route_after_retrieval,
        {
            "filter_context": "filter_context",
            "generate_answer": "generate_answer"
        }
    )

    workflow.add_edge("filter_context", "build_context")
    workflow.add_edge("build_context", "generate_answer")
    workflow.add_edge("generate_answer", "validate_grounding")
    workflow.add_edge("validate_grounding", "build_citations")
    workflow.add_edge("build_citations", END)

    return workflow.compile()
