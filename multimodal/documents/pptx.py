from typing import List, Dict, Any

class PptxParser:
    def parse_slides(self, file_path: str) -> List[Dict[str, Any]]:
        return [{"slide_number": 1, "notes": "", "text": []}]
