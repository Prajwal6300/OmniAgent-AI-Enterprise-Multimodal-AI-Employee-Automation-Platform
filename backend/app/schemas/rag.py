
from pydantic import BaseModel, ConfigDict, Field


class CitationData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    document_name: str
    page_number: int | None = None
    chunk_id: str
    relevance_score: float | None = None
    section: str | None = None


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="Question to answer from documents")
    document_id: str | None = Field(default=None, description="Optional document UUID to scope retrieval")
    top_k: int | None = Field(default=None, ge=1, le=20, description="Optional top K chunks")


class RAGQueryResponseData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    answer: str
    grounded: bool
    confidence: float
    citations: list[CitationData] = Field(default_factory=list)
    retrieved_chunks: int = 0
