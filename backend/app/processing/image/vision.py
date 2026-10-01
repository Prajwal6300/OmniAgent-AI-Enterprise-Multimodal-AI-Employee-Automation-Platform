from typing import Any


class VisionAnalyzer:
    def analyze_scene(self, image_path: str, prompt: str | None = None) -> dict[str, Any]:
        return {
            "description": "Visual scene analyzed.",
            "objects_detected": []
        }
