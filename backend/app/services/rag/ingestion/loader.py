from typing import List, Dict, Any

class DocumentLoader:
    def load(self, file_path: str) -> List[Dict[str, Any]]:
        return [{"text": "Extracted document content", "source": file_path}]
