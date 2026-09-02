from typing import List, Dict, Any

class ImageClassifier:
    def classify(self, image_path: str) -> List[Dict[str, Any]]:
        return [{"label": "document_scan", "confidence": 0.98}]
