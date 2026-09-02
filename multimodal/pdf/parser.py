from typing import Dict, Any

class PDFParser:
    def parse_metadata(self, file_path: str) -> Dict[str, Any]:
        return {
            "source": file_path,
            "page_count": 1,
            "format": "PDF-1.7"
        }
