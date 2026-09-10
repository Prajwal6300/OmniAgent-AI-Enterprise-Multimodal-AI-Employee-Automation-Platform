from datetime import datetime, timezone
from uuid import UUID
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    organization_id: UUID
    uploaded_by: Optional[UUID] = None
    file_name: str
    file_type: str
    file_size_bytes: int
    processing_status: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def extract_metadata(cls, data: Any) -> Any:
        if hasattr(data, "metadata_"):
            # SQLAlchemy model object
            meta = getattr(data, "metadata_", {})
            if isinstance(data, dict):
                data["metadata"] = meta
            else:
                setattr(data, "metadata", meta)
        if hasattr(data, "created_at") and getattr(data, "created_at") is None:
            if isinstance(data, dict):
                data["created_at"] = datetime.now(timezone.utc)
            else:
                setattr(data, "created_at", datetime.now(timezone.utc))
        return data


class DocumentAnalyzeRequest(BaseModel):
    document_id: UUID = Field(..., description="UUID of the uploaded document to analyze")
    task: str = Field(
        default="summarize",
        description="Analysis task: summarize, extract_information, classify, find_key_points, extract_entities, analyze_structure"
    )
    query: Optional[str] = Field(
        default=None,
        description="Optional custom query, question, or instruction regarding document content"
    )


class SourceReferenceSchema(BaseModel):
    page: Optional[int] = None
    section: Optional[str] = None
    paragraph: Optional[int] = None
    table_index: Optional[int] = None


class ExtractedFieldSchema(BaseModel):
    field: str
    value: Any
    source: Optional[SourceReferenceSchema] = None
    confidence: float = 1.0


class DocumentAnalysisResponseData(BaseModel):
    document_id: str
    document_type: str
    title: str
    summary: str
    key_points: List[str] = Field(default_factory=list)
    entities: Dict[str, Any] = Field(default_factory=dict)
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 1.0
    needs_ocr: bool = False
    warnings: List[str] = Field(default_factory=list)
    execution_time_ms: Optional[float] = None
