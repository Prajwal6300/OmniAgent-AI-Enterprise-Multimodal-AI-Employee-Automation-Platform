from typing import Dict, Any

class DocumentMetadataExtractor:
    def extract(self, file_path: str) -> Dict[str, Any]:
        return {"author": "Unknown", "title": file_path}
