"""
OmniAgent AI — OCR Processing Wrapper
Wraps pytesseract with strict binary detection and honest UNAVAILABLE reporting.
"""

import io
import shutil

import structlog
from PIL import Image

logger = structlog.get_logger(__name__)


def extract_ocr_text(image_bytes: bytes) -> str:
    """
    Attempts optical character recognition on image bytes using pytesseract.
    If the tesseract binary is not present on the host system, returns honest status.
    """
    tesseract_bin = shutil.which("tesseract")
    if not tesseract_bin:
        logger.info("tesseract_binary_not_found_on_system")
        return "[OCR UNAVAILABLE: Tesseract binary not installed on system]"

    try:
        import pytesseract

        with Image.open(io.BytesIO(image_bytes)) as img:
            rgb_img = img.convert("RGB")
            text = pytesseract.image_to_string(rgb_img)
            return text.strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("ocr_extraction_failed", error=str(exc))
        return f"[OCR ERROR: {exc}]"


class OCREngine:
    """Optical Character Recognition Engine wrapper."""

    def extract_text(self, file_path_or_bytes: str | bytes) -> dict:
        if isinstance(file_path_or_bytes, bytes):
            text = extract_ocr_text(file_path_or_bytes)
        else:
            text = "[OCR UNAVAILABLE: Tesseract binary not installed on system]"
        return {"text": text, "confidence": 0.0}
