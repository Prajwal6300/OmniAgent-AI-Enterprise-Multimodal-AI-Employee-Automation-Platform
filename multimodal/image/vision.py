from typing import Dict, Any

class VisionAnalyzer:
    def analyze_scene(self, image_path: str, prompt: str = None) -> Dict[str, Any]:
        return {
            "description": "Visual scene analyzed.",
            "objects_detected": []
        }
