from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator


class Citation(BaseModel):
    """
    Verifiable source citation strictly tied to an actual retrieved document chunk.
    Never fabricated.
    """
    document_id: str = Field(..., description="UUID of the parent document artifact")
    document_name: str = Field(..., description="Human-readable filename of the document")
    page_number: int | None = Field(default=None, description="1-indexed physical page number where available")
    chunk_id: str = Field(..., description="UUID of the retrieved document chunk")
    relevance_score: float | None = Field(default=None, description="Cosine similarity or reranked relevance score")
    section: str | None = Field(default=None, description="Section heading or title where available")


class RetrievedChunk(BaseModel):
    """
    Internal representation of a retrieved document passage with tenant and spatial metadata.
    """
    chunk_id: str
    document_id: str
    organization_id: str
    document_name: str
    page_number: int | None = None
    section: str | None = None
    chunk_index: int = 0
    content: str
    similarity_score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGQuery(BaseModel):
    """
    Search parameters for retrieving semantic context.
    Maintains compatibility with legacy stub while supporting production RAG parameters.
    """
    query: str = Field(..., min_length=1, description="Natural language question or query string")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of chunks to retrieve")
    document_id: str | None = Field(default=None, description="Optional document UUID to filter retrieval")
    similarity_threshold: float = Field(default=0.4, ge=0.0, le=1.0, description="Minimum similarity cutoff")


class RAGQueryRequest(BaseModel):
    """
    Public API request payload for RAG querying.
    """
    question: str = Field(..., min_length=1, max_length=2000, description="User question to answer from documents")
    document_id: str | None = Field(default=None, description="Optional specific document ID filter")
    top_k: int | None = Field(default=None, ge=1, le=20, description="Optional top K chunks to retrieve")


class RAGResponse(BaseModel):
    """
    Production-quality structured output produced by RAG Agent.
    """
    answer: str = Field(..., description="Synthesized grounded answer or fallback statement")
    grounded: bool = Field(default=True, description="True if answer is verified to be supported by retrieved context")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    citations: list[Citation] = Field(default_factory=list, description="Verified source citations")
    retrieved_chunks: int = Field(default=0, description="Number of retrieved chunks used in context")

    # Backward compatibility attributes for legacy stub: passages, sources
    passages: list[str] = Field(default_factory=list, description="Legacy list of retrieved text passages")
    sources: list[str] = Field(default_factory=list, description="Legacy list of source names")

    query: str | None = Field(default=None, description="Original query evaluated")
    latency_ms: float | None = Field(default=None, description="Total execution time in milliseconds")

    @model_validator(mode="after")
    def populate_compatibility_fields(self) -> "RAGResponse":
        if not self.sources and self.citations:
            self.sources = [f"{c.document_name} (Page {c.page_number})" if c.page_number else c.document_name for c in self.citations]
        return self

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, round(v, 4)))
