from pathlib import Path
from typing import Any

from agents.document.exceptions import (
    DocumentExtractionError,
    DocumentValidationError,
)
from agents.document.extractor import (
    MAX_SAFE_TEXT_LENGTH,
    extract_text_from_docx,
    extract_text_from_pdf,
    extract_text_from_txt,
    validate_file_metadata,
)
from agents.document.prompts import DOCUMENT_SYSTEM_PROMPT
from agents.document.providers import (
    BaseDocumentLLMProvider,
    get_default_document_llm_provider,
)
from agents.document.router import heuristic_classify_document
from agents.document.schemas import DocumentPage, DocumentType
from agents.document.state import DocumentState


async def validate_document_node(state: DocumentState) -> dict[str, Any]:
    """
    Node 1: Validates document presence, metadata, file size, and extension security.
    """
    filename = state.get("filename", "")
    file_bytes = state.get("file_bytes")
    file_path = state.get("file_path", "")
    mime_type = state.get("mime_type")

    # If bytes not present in state, try reading from file_path safely
    if not file_bytes and file_path:
        path_obj = Path(file_path)
        if not path_obj.exists():
            return {
                "status": "FAILED_VALIDATION",
                "error": f"Document file not found at path: {file_path}",
                "confidence": 0.0
            }
        try:
            file_bytes = path_obj.read_bytes()
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "FAILED_VALIDATION",
                "error": f"Unable to read document file: {exc!s}",
                "confidence": 0.0
            }

    if not filename and file_path:
        filename = Path(file_path).name

    try:
        validate_file_metadata(
            filename=filename or "document.bin",
            file_bytes=file_bytes or b"",
            mime_type=mime_type
        )
        return {
            "status": "VALIDATED",
            "filename": filename,
            "file_bytes": file_bytes,
            "file_size": len(file_bytes) if file_bytes else 0,
            "error": None
        }
    except DocumentValidationError as err:
        return {
            "status": "FAILED_VALIDATION",
            "error": str(err),
            "confidence": 0.0
        }


async def extract_text_node(state: DocumentState) -> dict[str, Any]:
    """
    Node 2: Extracts textual content, pages, tables, and sections while detecting OCR requirements.
    """
    if state.get("status") == "FAILED_VALIDATION":
        return {}

    filename = state.get("filename", "")
    file_bytes = state.get("file_bytes")
    ext = Path(filename).suffix.lower()

    pages: list[DocumentPage] = []
    sections: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []
    needs_ocr = False
    warnings: list[str] = list(state.get("warnings", []))

    try:
        if ext == ".pdf":
            extracted_pages, ocr_needed, ocr_warn = extract_text_from_pdf(file_bytes)
            pages = extracted_pages
            needs_ocr = ocr_needed
            if ocr_warn:
                warnings.append(ocr_warn)

        elif ext == ".docx":
            extracted_pages, docx_sections, docx_tables = extract_text_from_docx(file_bytes)
            pages = extracted_pages
            sections = [s.model_dump() for s in docx_sections]
            tables = [t.model_dump() for t in docx_tables]

        elif ext == ".txt":
            pages = extract_text_from_txt(file_bytes)

        else:
            return {
                "status": "FAILED_EXTRACTION",
                "error": f"Unsupported file extension: {ext}",
                "confidence": 0.0
            }

        extracted_text = "\n\n".join(p.text for p in pages if p.text.strip())

        return {
            "status": "EXTRACTED",
            "pages": [p.model_dump() for p in pages],
            "extracted_text": extracted_text,
            "sections": sections,
            "tables": tables,
            "needs_ocr": needs_ocr,
            "warnings": warnings,
            "error": None
        }

    except DocumentExtractionError as err:
        return {
            "status": "FAILED_EXTRACTION",
            "error": str(err),
            "confidence": 0.0
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "FAILED_EXTRACTION",
            "error": f"Document parsing failed: {exc!s}",
            "confidence": 0.0
        }


async def normalize_content_node(state: DocumentState) -> dict[str, Any]:
    """
    Node 3: Cleans, sanitizes, and applies maximum text length safeguards.
    """
    if state.get("status") in ["FAILED_VALIDATION", "FAILED_EXTRACTION"]:
        return {}

    raw_text = state.get("extracted_text", "")
    warnings = list(state.get("warnings", []))

    # Text length safeguard for very large documents
    if len(raw_text) > MAX_SAFE_TEXT_LENGTH:
        raw_text = raw_text[:MAX_SAFE_TEXT_LENGTH]
        warnings.append(
            f"Document text exceeds safe single-pass limit ({MAX_SAFE_TEXT_LENGTH:,} characters). "
            f"Analysis truncated to first {MAX_SAFE_TEXT_LENGTH:,} characters."
        )

    return {
        "status": "NORMALIZED",
        "extracted_text": raw_text,
        "warnings": warnings
    }


async def classify_document_node(state: DocumentState) -> dict[str, Any]:
    """
    Node 4: Classifies the document into domain taxonomy (INVOICE, REPORT, POLICY, etc.).
    """
    if state.get("status") in ["FAILED_VALIDATION", "FAILED_EXTRACTION"]:
        return {}

    text = state.get("extracted_text", "")
    filename = state.get("filename", "")

    doc_type, confidence, inferred_title = heuristic_classify_document(text, filename)

    return {
        "status": "CLASSIFIED",
        "document_type": doc_type.value,
        "title": inferred_title,
        "confidence": confidence
    }


async def understand_document_node(
    state: DocumentState,
    provider: BaseDocumentLLMProvider | None = None
) -> dict[str, Any]:
    """
    Node 5: Conducts structured extraction, summarization, or domain understanding.
    Defends against prompt injection, prevents hallucinations, and tracks citations.
    """
    if state.get("status") in ["FAILED_VALIDATION", "FAILED_EXTRACTION"]:
        return {}

    llm_provider = provider or get_default_document_llm_provider()
    text = state.get("extracted_text", "")
    pages_raw = state.get("pages", [])
    pages = [DocumentPage(**p) for p in pages_raw]
    task = state.get("task", "summarize")
    query = state.get("query")
    doc_id = state.get("document_id", "doc_unknown")
    doc_type = state.get("document_type", DocumentType.UNKNOWN.value)
    warnings = list(state.get("warnings", []))
    needs_ocr = state.get("needs_ocr", False)

    # Scanned image PDF defense: never hallucinate content that doesn't exist
    if needs_ocr:
        return {
            "status": "UNDERSTOOD",
            "result": {
                "document_id": doc_id,
                "document_type": doc_type,
                "title": state.get("title", "Scanned Document"),
                "summary": "OCR required: Scanned document contains no digital text layer. Text cannot be extracted without an OCR engine.",
                "key_points": ["No machine-readable text found in PDF pages.", "Optical Character Recognition (OCR) is required."],
                "entities": {},
                "structured_data": {},
                "pages": [p.model_dump() for p in pages],
                "sources": [],
                "confidence": 0.0,
                "needs_ocr": True,
                "warnings": warnings
            }
        }

    try:
        understanding_json = await llm_provider.generate_understanding_json(
            document_text=text,
            pages=pages,
            task=task,
            query=query,
            system_prompt=DOCUMENT_SYSTEM_PROMPT
        )

        # Ensure document_id and pages are attached
        understanding_json["document_id"] = doc_id
        if "pages" not in understanding_json or not understanding_json["pages"]:
            understanding_json["pages"] = [p.model_dump() for p in pages]
        understanding_json["needs_ocr"] = False
        understanding_json["warnings"] = list(set(warnings + understanding_json.get("warnings", [])))

        return {
            "status": "UNDERSTOOD",
            "result": understanding_json,
            "confidence": understanding_json.get("confidence", state.get("confidence", 0.9))
        }

    except Exception as exc:  # noqa: BLE001
        return {
            "status": "FAILED_UNDERSTANDING",
            "error": f"Document understanding failure: {exc!s}",
            "confidence": 0.0
        }


async def validate_result_node(state: DocumentState) -> dict[str, Any]:
    """
    Node 6: Validates final structured payload against schema, clamps confidence, and returns final state.
    """
    status = state.get("status")
    doc_id = state.get("document_id", "doc_unknown")

    if status in ["FAILED_VALIDATION", "FAILED_EXTRACTION", "FAILED_UNDERSTANDING"]:
        err_msg = state.get("error", "Document processing error occurred.")
        return {
            "status": "FAILED",
            "result": {
                "document_id": doc_id,
                "document_type": DocumentType.UNKNOWN.value,
                "title": "Error",
                "summary": err_msg,
                "key_points": [],
                "entities": {},
                "structured_data": {},
                "pages": [],
                "sources": [],
                "confidence": 0.0,
                "needs_ocr": False,
                "warnings": [err_msg]
            }
        }

    raw_result = state.get("result", {})
    confidence = raw_result.get("confidence", state.get("confidence", 1.0))
    clamped_conf = max(0.0, min(1.0, float(confidence)))
    raw_result["confidence"] = round(clamped_conf, 4)

    return {
        "status": "COMPLETED",
        "result": raw_result,
        "confidence": raw_result["confidence"]
    }
