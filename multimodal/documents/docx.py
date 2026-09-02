from typing import Dict, Any

class DocxParser:
    def parse(self, file_path: str) -> Dict[str, Any]:
        return {"paragraphs": [], "metadata": {"file": file_path}}
