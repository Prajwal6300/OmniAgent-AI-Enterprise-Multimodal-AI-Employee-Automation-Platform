from typing import Any


class PptxParser:
    def parse_slides(self, file_path: str) -> list[dict[str, Any]]:
        return [{"slide_number": 1, "notes": "", "text": []}]
