from typing import Any


class OCREngine:
    def extract_text(self, image_path: str) -> dict[str, Any]:
        return {"text": "OCR recognized text.", "confidence": 0.95}
