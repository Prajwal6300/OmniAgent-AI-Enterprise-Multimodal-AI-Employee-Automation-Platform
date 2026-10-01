from typing import Any


class DocxParser:
    def parse(self, file_path: str) -> dict[str, Any]:
        return {"paragraphs": [], "metadata": {"file": file_path}}
