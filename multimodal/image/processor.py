from typing import Dict, Any

class ImageProcessor:
    def preprocess(self, image_path: str) -> Dict[str, Any]:
        return {"status": "preprocessed", "path": image_path}
