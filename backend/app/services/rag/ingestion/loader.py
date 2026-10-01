from typing import Any


class DocumentLoader:
    def load(self, file_path: str) -> list[dict[str, Any]]:
        return [{"text": "Extracted document content", "source": file_path}]
