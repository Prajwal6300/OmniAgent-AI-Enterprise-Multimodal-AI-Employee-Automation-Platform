"""
OmniAgent AI — PDF Processing Module
Provides sequential, page-capped text extraction using pypdf to prevent memory exhaustion (OOM).
"""

import io
from typing import Any

import structlog
from pypdf import PdfReader

logger = structlog.get_logger(__name__)

PDF_MAGIC_BYTES = b"%PDF"


def extract_pdf_text(
    file_bytes: bytes,
    max_pages: int = 100,
) -> list[dict[str, Any]]:
    """
    Extracts text page by page from raw PDF bytes.
    Enforces magic bytes and page limits to avoid memory exhaustion attacks.
    """
    if not file_bytes.startswith(PDF_MAGIC_BYTES):
        raise ValueError("Invalid PDF file: magic bytes header mismatch")

    reader = PdfReader(io.BytesIO(file_bytes))
    total_pages = len(reader.pages)

    if total_pages > max_pages:
        logger.warning(
            "pdf_pages_exceeded_cap",
            total_pages=total_pages,
            cap=max_pages,
        )

    pages_to_process = min(total_pages, max_pages)
    extracted: list[dict[str, Any]] = []

    for page_num in range(pages_to_process):
        page = reader.pages[page_num]
        text = page.extract_text() or ""
        extracted.append({
            "page_number": page_num + 1,
            "text": text.strip(),
            "character_count": len(text),
        })

    return extracted
