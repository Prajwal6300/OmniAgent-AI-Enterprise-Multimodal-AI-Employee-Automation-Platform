from typing import Dict, Any

class VideoProcessor:
    def inspect(self, video_path: str) -> Dict[str, Any]:
        return {"duration_sec": 60, "fps": 30, "resolution": "1920x1080"}
