from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class DocumentType(str, Enum):
    INVOICE = "INVOICE"
    REPORT = "REPORT"
    POLICY = "POLICY"
    CONTRACT = "CONTRACT"
    TECHNICAL_MANUAL = "TECHNICAL_MANUAL"
    RESUME = "RESUME"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    GENERAL_DOCUMENT = "GENERAL_DOCUMENT"
    UNKNOWN = "UNKNOWN"


class DocumentTask(str, Enum):
    SUMMARIZE = "summarize"
    EXTRACT_INFORMATION = "extract_information"
    CLASSIFY = "classify"
    FIND_KEY_POINTS = "find_key_points"
    EXTRACT_ENTITIES = "extract_entities"
    ANALYZE_STRUCTURE = "analyze_structure"


class SourceReference(BaseModel):
    page: int | None = Field(default=None, description="PDF page number (1-indexed)")
    section: str | None = Field(default=None, description="Document section or heading title")
    paragraph: int | None = Field(default=None, description="Paragraph index (1-indexed)")
    table_index: int | None = Field(default=None, description="Table index if within a table")


class ExtractedField(BaseModel):
    field: str = Field(..., description="Field or attribute identifier, e.g. invoice_total")
    value: Any = Field(..., description="Extracted factual value, or 'Not found in the provided document'")
    source: SourceReference | None = Field(default=None, description="Source citation reference")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")


class DocumentPage(BaseModel):
    page_number: int = Field(..., description="1-indexed page number")
    text: str = Field(default="", description="Extracted raw text of the page")
    char_count: int = Field(default=0, description="Character count in this page")


class DocumentSection(BaseModel):
    title: str = Field(..., description="Section title or heading")
    content: str = Field(default="", description="Textual content within the section")
    section_type: str = Field(default="section", description="heading, paragraph, or callout")
    page_number: int | None = Field(default=None, description="Associated page number")


class DocumentTable(BaseModel):
    headers: list[str] = Field(default_factory=list, description="Column header labels")
    rows: list[list[str]] = Field(default_factory=list, description="Row cell contents")
    page_number: int | None = Field(default=None, description="Page where table is located")
    title: str | None = Field(default=None, description="Table caption or title if found")


class InvoiceData(BaseModel):
    vendor: str | None = Field(default=None, description="Vendor or supplier entity name")
    invoice_number: str | None = Field(default=None, description="Invoice unique number or ID")
    date: str | None = Field(default=None, description="Invoice issuance date")
    subtotal: str | None = Field(default=None, description="Subtotal amount before tax")
    tax: str | None = Field(default=None, description="Tax or VAT amount")
    total: str | None = Field(default=None, description="Total invoice amount payable")
    currency: str | None = Field(default=None, description="Currency code or symbol, e.g. INR, USD, EUR")
    line_items: list[dict[str, Any]] = Field(default_factory=list, description="Itemized billing breakdown")


class PolicyData(BaseModel):
    summary: str | None = Field(default=None, description="Executive summary of the policy")
    important_rules: list[str] = Field(default_factory=list, description="Mandatory organizational rules")
    eligibility: list[str] = Field(default_factory=list, description="Who is covered or eligible")
    restrictions: list[str] = Field(default_factory=list, description="Limitations, constraints, or exclusions")
    relevant_sections: list[str] = Field(default_factory=list, description="Referenced policy clauses or sections")


class TechnicalManualData(BaseModel):
    summary: str | None = Field(default=None, description="Technical manual summary")
    key_instructions: list[str] = Field(default_factory=list, description="Step-by-step operating instructions")
    warnings: list[str] = Field(default_factory=list, description="Safety cautions and warnings")
    relevant_sections: list[str] = Field(default_factory=list, description="Cited manual sections")


class ReportData(BaseModel):
    executive_summary: str | None = Field(default=None, description="High-level report summary")
    important_findings: list[str] = Field(default_factory=list, description="Primary discoveries or findings")
    numbers: list[str] = Field(default_factory=list, description="Key numerical metrics and KPIs")
    conclusions: list[str] = Field(default_factory=list, description="Final determinations or next steps")
    warnings: list[str] = Field(default_factory=list, description="Risk factors, caveats, or anomalies")


class DocumentAnalysisResult(BaseModel):
    document_id: str = Field(..., description="Unique document UUID")
    document_type: str = Field(default=DocumentType.UNKNOWN.value, description="Classified document type")
    title: str = Field(default="Document", description="Extracted or inferred document title")
    summary: str = Field(default="", description="High-level summary of the document")
    key_points: list[str] = Field(default_factory=list, description="Essential key takeaways")
    entities: dict[str, Any] = Field(default_factory=dict, description="Identified named entities")
    structured_data: dict[str, Any] = Field(default_factory=dict, description="Domain-specific parsed schema data")
    pages: list[DocumentPage] = Field(default_factory=list, description="Extracted individual pages with citations")
    sources: list[dict[str, Any]] = Field(default_factory=list, description="Exact source page or section references")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Overall understanding confidence")
    needs_ocr: bool = False
    warnings: list[str] = Field(default_factory=list, description="Limitations, truncation alerts, or OCR notices")
    execution_time_ms: float | None = Field(default=None, description="Processing duration in milliseconds")

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        if v < 0.0:
            return 0.0
        if v > 1.0:
            return 1.0
        return round(v, 4)


# Backward-compatibility schema
class DocumentExtractionResult(BaseModel):
    document_id: str
    tables: list[dict[str, Any]] = Field(default_factory=list)
    key_value_pairs: dict[str, str] = Field(default_factory=dict)
