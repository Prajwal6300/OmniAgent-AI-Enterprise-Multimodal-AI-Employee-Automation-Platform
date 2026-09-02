from typing import Dict, Any

class MetadataExtractor:
    def enrich(self, chunk: str, source_doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": source_doc.get("source"),
            "length": len(chunk)
        }
