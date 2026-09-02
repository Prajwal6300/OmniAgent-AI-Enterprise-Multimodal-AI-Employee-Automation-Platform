from typing import List, Dict, Any

class PDFExtractor:
    def extract_pages(self, file_path: str) -> List[Dict[str, Any]]:
        return [{"page": 1, "text": "Extracted PDF content stream."}]
