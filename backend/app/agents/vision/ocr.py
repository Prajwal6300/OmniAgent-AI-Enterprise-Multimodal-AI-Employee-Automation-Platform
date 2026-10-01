"""
OCR Provider Abstraction and Engine Integration.
Provides a clean protocol and implementations for optical character recognition.
Honestly reports engine availability—NEVER produces fabricated OCR results.
"""

import asyncio
import os
from typing import Any, Protocol

try:
    from app.core.config import settings
except ImportError:
    try:
        from backend.app.core.config import settings
    except ImportError:

        class SettingsFallback:
            VISION_OCR_ENABLED = True

        settings = SettingsFallback()

try:
    from app.core.logging import logger
except ImportError:
    try:
        from backend.app.core.logging import logger
    except ImportError:
        import logging

        logger = logging.getLogger("omniagent.vision.ocr")

from app.agents.vision.schemas import ProcessorStatus


class OCRProvider(Protocol):
    """Protocol defining optical character recognition interface."""

    async def extract_text(
        self, image_path: str | None = None, image_bytes: bytes | None = None
    ) -> dict[str, Any]:
        """
        Extracts textual content and bounding regions from an image.
        Returns:
            {
                "text": str,
                "confidence": float,
                "status": str,
                "regions": list[dict],
                "message": str | None
            }
        """
        ...


class SystemOCRProvider:
    """
    Production OCR provider attempting to leverage installed system engines (e.g. pytesseract).
    If no OCR engine is available or enabled, honestly reports UNAVAILABLE without fabricating results.
    """

    def __init__(self, enabled: bool | None = None):
        self.enabled = (
            enabled
            if enabled is not None
            else getattr(settings, "VISION_OCR_ENABLED", True)
        )
        self._engine_checked = False
        self._engine_available = False
        self._check_engine()

    def _check_engine(self) -> None:
        if not self.enabled:
            self._engine_available = False
            self._engine_checked = True
            return

        try:
            import pytesseract  # type: ignore

            # Check if tesseract binary is actually reachable
            # (can test with get_tesseract_version)
            pytesseract.get_tesseract_version()
            self._engine_available = True
        except Exception:  # noqa: BLE001
            self._engine_available = False
        finally:
            self._engine_checked = True

    async def extract_text(
        self, image_path: str | None = None, image_bytes: bytes | None = None
    ) -> dict[str, Any]:
        if not self.enabled:
            return {
                "text": "",
                "confidence": 0.0,
                "status": ProcessorStatus.SKIPPED.value,
                "regions": [],
                "message": "OCR is disabled in application configuration.",
            }

        if not self._engine_available:
            return {
                "text": "",
                "confidence": 0.0,
                "status": ProcessorStatus.UNAVAILABLE.value,
                "regions": [],
                "message": "OCR engine (Tesseract) is not installed or configured on the host system.",
            }

        def _do_ocr() -> dict[str, Any]:
            import io

            import pytesseract
            from PIL import Image

            if image_bytes:
                img = Image.open(io.BytesIO(image_bytes))
            elif image_path and os.path.exists(image_path):
                img = Image.open(image_path)
            else:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "status": ProcessorStatus.FAILED.value,
                    "regions": [],
                    "message": "No valid image source provided for OCR extraction.",
                }

            # Run tesseract data extraction
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            n_boxes = len(data["text"])
            recognized_words = []
            confidences = []
            regions = []

            for i in range(n_boxes):
                word = data["text"][i].strip()
                conf = float(data["conf"][i])
                if word and conf > 0:
                    recognized_words.append(word)
                    confidences.append(conf / 100.0)
                    regions.append(
                        {
                            "text": word,
                            "confidence": round(conf / 100.0, 4),
                            "bbox": [
                                float(data["left"][i]),
                                float(data["top"][i]),
                                float(data["width"][i]),
                                float(data["height"][i]),
                            ],
                        }
                    )

            full_text = " ".join(recognized_words)
            avg_conf = (sum(confidences) / len(confidences)) if confidences else 0.0

            return {
                "text": full_text,
                "confidence": round(avg_conf, 4),
                "status": ProcessorStatus.SUCCESS.value,
                "regions": regions,
                "message": None,
            }

        try:
            return await asyncio.to_thread(_do_ocr)
        except Exception as exc:  # noqa: BLE001
            logger.warning("ocr_execution_failed", error=str(exc))
            return {
                "text": "",
                "confidence": 0.0,
                "status": ProcessorStatus.FAILED.value,
                "regions": [],
                "message": f"OCR processing failed: {exc!s}",
            }


def get_ocr_provider(provider_type: str | None = None) -> OCRProvider:
    """Factory retrieving the configured OCR provider."""
    return SystemOCRProvider()
