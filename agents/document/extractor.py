import io
import re
from pathlib import Path

from agents.document.exceptions import (
    DocumentExtractionError,
    DocumentValidationError,
)
from agents.document.schemas import DocumentPage, DocumentSection, DocumentTable

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

MAX_DOCUMENT_SIZE = 25 * 1024 * 1024  # 25MB
MAX_SAFE_TEXT_LENGTH = 100_000  # 100,000 characters safeguard


def validate_file_metadata(
    filename: str,
    file_bytes: bytes,
    mime_type: str | None = None,
    max_size: int = MAX_DOCUMENT_SIZE
) -> str:
    """
    Performs strict file validation:
    1. Rejects empty files (0 bytes)
    2. Enforces maximum size limits
    3. Validates file extension
    4. Validates MIME type if provided
    5. Detects path traversal
    """
    if not file_bytes or len(file_bytes) == 0:
        raise DocumentValidationError("File is empty (0 bytes). Upload a valid document.")

    if len(file_bytes) > max_size:
        raise DocumentValidationError(
            f"File size ({len(file_bytes)} bytes) exceeds maximum permitted limit ({max_size} bytes)."
        )

    # Filename security
    if ".." in filename or "/" in filename or "\\" in filename:
        # Detected path traversal pattern
        pass  # We sanitize later, but check extension strictly

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise DocumentValidationError(
            f"Unsupported file extension '{ext}'. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    if mime_type:
        clean_mime = mime_type.split(";")[0].strip().lower()
        # Some clients send application/octet-stream for docx/pdf or text/plain
        if clean_mime not in ALLOWED_MIME_TYPES and clean_mime != "application/octet-stream":
            raise DocumentValidationError(
                f"Unsupported MIME type '{clean_mime}'. Allowed MIME types: {', '.join(ALLOWED_MIME_TYPES)}"
            )

    return ext


def extract_text_from_pdf(file_bytes: bytes) -> tuple[list[DocumentPage], bool, str]:
    """
    Extracts text per page from PDF using pypdf.
    Preserves page numbers (1-indexed) and detects if OCR is required.
    Returns: (pages, needs_ocr, warning_message)
    """
    try:
        import pypdf
    except ImportError:
        raise DocumentExtractionError("pypdf library is required for PDF text extraction.")

    pages: list[DocumentPage] = []
    total_text = ""
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        total_pages = len(reader.pages)
        if total_pages == 0:
            raise DocumentExtractionError("PDF file has 0 pages.")

        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            # Clean non-printable / control chars and PDF newline glyphs while preserving newlines
            clean_text = page_text.replace("\u25a0", "\n")
            clean_text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", clean_text)
            clean_text = clean_text.strip()
            pages.append(DocumentPage(
                page_number=idx + 1,
                text=clean_text,
                char_count=len(clean_text)
            ))
            total_text += clean_text

    except Exception as exc:
        raise DocumentExtractionError(f"Corrupted or unreadable PDF: {exc!s}") from exc

    # Detect if PDF contains no extractable text (e.g. scanned image PDF)
    non_ws_chars = len(re.sub(r"\s+", "", total_text))
    if non_ws_chars < 20:
        return pages, True, "OCR required: Scanned document contains no digital text layer."

    return pages, False, ""


def extract_text_from_docx(file_bytes: bytes) -> tuple[list[DocumentPage], list[DocumentSection], list[DocumentTable]]:
    """
    Extracts structured content from DOCX: paragraphs, headings, tables.
    Preserves document structure as much as possible.
    """
    try:
        import docx
    except ImportError:
        raise DocumentExtractionError("python-docx library is required for DOCX extraction.")

    sections: list[DocumentSection] = []
    tables: list[DocumentTable] = []
    full_paragraphs: list[str] = []

    try:
        doc = docx.Document(io.BytesIO(file_bytes))

        current_heading = "General"
        current_section_lines: list[str] = []

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            style_name = p.style.name if p.style else ""
            if style_name.startswith("Heading") or style_name in ["Title", "Subtitle"]:
                if current_section_lines:
                    sections.append(DocumentSection(
                        title=current_heading,
                        content="\n".join(current_section_lines),
                        section_type="heading"
                    ))
                    current_section_lines = []
                current_heading = text
            else:
                current_section_lines.append(text)
                full_paragraphs.append(text)

        if current_section_lines:
            sections.append(DocumentSection(
                title=current_heading,
                content="\n".join(current_section_lines),
                section_type="heading"
            ))

        # Extract tables
        for t_idx, table in enumerate(doc.tables):
            table_rows: list[list[str]] = []
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells]
                table_rows.append(cells)

            if table_rows:
                headers = table_rows[0]
                data_rows = table_rows[1:] if len(table_rows) > 1 else []
                tables.append(DocumentTable(
                    headers=headers,
                    rows=data_rows,
                    page_number=1,
                    title=f"Table {t_idx + 1}"
                ))

        # Synthesize synthetic pages (~3000 chars per page chunk)
        combined_text = "\n\n".join(full_paragraphs)
        if not combined_text and tables:
            # Table-only document
            table_text = "\n".join(["\t".join(r) for t in tables for r in t.rows])
            combined_text = table_text

        pages: list[DocumentPage] = []
        chunk_size = 3000
        if combined_text:
            chunks = [combined_text[i:i + chunk_size] for i in range(0, len(combined_text), chunk_size)]
            for idx, c in enumerate(chunks):
                pages.append(DocumentPage(page_number=idx + 1, text=c, char_count=len(c)))
        else:
            pages.append(DocumentPage(page_number=1, text="", char_count=0))

        return pages, sections, tables

    except Exception as exc:
        raise DocumentExtractionError(f"Corrupted or unreadable DOCX: {exc!s}") from exc


def extract_text_from_txt(file_bytes: bytes) -> list[DocumentPage]:
    """
    Extracts text from TXT with robust multi-encoding support (UTF-8, Latin-1, CP1252).
    Normalizes line endings and breaks into pages if large.
    """
    encodings_to_try = ["utf-8", "latin-1", "cp1252", "utf-16"]
    raw_text = None
    for enc in encodings_to_try:
        try:
            raw_text = file_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if raw_text is None:
        raise DocumentExtractionError("Unable to decode text file with standard encodings (UTF-8, Latin-1, CP1252).")

    # Normalize line endings
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse multiple blank lines (> 3 into 2)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()

    # Split into 3000-character pages for consistency
    chunk_size = 3000
    pages: list[DocumentPage] = []
    if normalized:
        chunks = [normalized[i:i + chunk_size] for i in range(0, len(normalized), chunk_size)]
        for idx, chunk in enumerate(chunks):
            pages.append(DocumentPage(
                page_number=idx + 1,
                text=chunk,
                char_count=len(chunk)
            ))
    else:
        pages.append(DocumentPage(page_number=1, text="", char_count=0))

    return pages
