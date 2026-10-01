from typing import Any


class PDFExtractor:
    def extract_pages(self, file_path: str) -> list[dict[str, Any]]:
        return [{"page": 1, "text": "Extracted PDF content stream."}]
