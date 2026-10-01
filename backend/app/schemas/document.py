from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    organization_id: UUID
    uploaded_by: UUID | None = None
    file_name: str
    file_type: str
    file_size_bytes: int
    processing_status: str
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def extract_metadata(cls, data: Any) -> Any:
        if hasattr(data, "metadata_"):
            # SQLAlchemy model object
            meta = getattr(data, "metadata_", {})
            if isinstance(data, dict):
                data["metadata"] = meta
            else:
                data.metadata = meta
        if hasattr(data, "created_at") and data.created_at is None:
            if isinstance(data, dict):
                data["created_at"] = datetime.now(UTC)
            else:
                data.created_at = datetime.now(UTC)
        return data


class DocumentAnalyzeRequest(BaseModel):
    document_id: UUID = Field(..., description="UUID of the uploaded document to analyze")
    task: str = Field(
        default="summarize",
        description="Analysis task: summarize, extract_information, classify, find_key_points, extract_entities, analyze_structure"
    )
    query: str | None = Field(
        default=None,
        description="Optional custom query, question, or instruction regarding document content"
    )


class SourceReferenceSchema(BaseModel):
    page: int | None = None
    section: str | None = None
    paragraph: int | None = None
    table_index: int | None = None


class ExtractedFieldSchema(BaseModel):
    field: str
    value: Any
    source: SourceReferenceSchema | None = None
    confidence: float = 1.0


class DocumentAnalysisResponseData(BaseModel):
    document_id: str
    document_type: str
    title: str
    summary: str
    key_points: list[str] = Field(default_factory=list)
    entities: dict[str, Any] = Field(default_factory=dict)
    structured_data: dict[str, Any] = Field(default_factory=dict)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 1.0
    needs_ocr: bool = False
    warnings: list[str] = Field(default_factory=list)
    execution_time_ms: float | None = None
