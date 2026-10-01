from typing import Any


class ImageClassifier:
    def classify(self, image_path: str) -> list[dict[str, Any]]:
        return [{"label": "document_scan", "confidence": 0.98}]
