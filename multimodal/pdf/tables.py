from typing import List, Dict, Any

class PDFTableExtractor:
    def extract_tables(self, file_path: str) -> List[Dict[str, Any]]:
        return [{"table_id": 1, "headers": ["Item", "Qty", "Price"], "rows": []}]
