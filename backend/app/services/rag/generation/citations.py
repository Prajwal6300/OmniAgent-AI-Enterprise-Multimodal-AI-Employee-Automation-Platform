from typing import List, Dict, Any

class CitationExtractor:
    def extract_citations(self, response_text: str, source_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [{"chunk_id": c.get("id"), "source": c.get("source")} for c in source_chunks]
