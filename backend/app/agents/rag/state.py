from typing import Any, TypedDict


class RAGState(TypedDict, total=False):
    """
    Strongly typed state dictionary flowing through the RAG Agent LangGraph workflow.
    """
    request_id: str
    user_id: str
    organization_id: str
    conversation_id: str | None

    # Query input and processing
    question: str
    normalized_query: str
    document_id_filter: str | None
    top_k: int
    similarity_threshold: float

    # Vector representations and filters
    query_embedding: list[float]
    filters: dict[str, Any]

    # Retrieval and context construction
    retrieved_chunks: list[dict[str, Any]]
    filtered_chunks: list[dict[str, Any]]
    context: str

    # Generation and grounding
    raw_answer: str
    answer: str
    grounded: bool
    confidence: float

    # Citations and metrics
    citations: list[dict[str, Any]]
    retrieved_chunks_count: int

    # Workflow lifecycle and telemetry
    status: str
    error: str | None
    latency_ms: float
