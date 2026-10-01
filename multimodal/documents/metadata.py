from typing import Any


class DocumentMetadataExtractor:
    def extract(self, file_path: str) -> dict[str, Any]:
        return {"author": "Unknown", "title": file_path}
