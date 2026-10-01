from typing import Any


class MetadataExtractor:
    def enrich(self, chunk: str, source_doc: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": source_doc.get("source"),
            "length": len(chunk)
        }
