from typing import Any


class PDFTableExtractor:
    def extract_tables(self, file_path: str) -> list[dict[str, Any]]:
        return [{"table_id": 1, "headers": ["Item", "Qty", "Price"], "rows": []}]
