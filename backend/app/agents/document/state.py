from typing import Any, TypedDict


class DocumentState(TypedDict, total=False):
    """
    Strongly typed state dictionary flowing through the Document Agent LangGraph workflow.
    """
    request_id: str
    user_id: str
    organization_id: str
    document_id: str

    filename: str
    file_path: str
    file_bytes: bytes | None
    mime_type: str
    file_size: int

    document_type: str
    title: str

    pages: list[dict[str, Any]]
    extracted_text: str
    sections: list[dict[str, Any]]
    tables: list[dict[str, Any]]

    task: str
    query: str | None

    result: dict[str, Any]
    confidence: float
    needs_ocr: bool
    warnings: list[str]

    status: str
    error: str | None
