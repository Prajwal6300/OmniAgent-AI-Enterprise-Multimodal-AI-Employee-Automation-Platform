from typing import Dict, Any

class OCREngine:
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        return {"text": "OCR recognized text.", "confidence": 0.95}
