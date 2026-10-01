from typing import Any


class CitationExtractor:
    def extract_citations(self, response_text: str, source_chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{"chunk_id": c.get("id"), "source": c.get("source")} for c in source_chunks]
