from typing import Any


class ImageProcessor:
    def preprocess(self, image_path: str) -> dict[str, Any]:
        return {"status": "preprocessed", "path": image_path}
