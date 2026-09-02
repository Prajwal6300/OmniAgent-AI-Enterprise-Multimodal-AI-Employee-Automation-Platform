from typing import Dict, List, Any

class ExcelProcessor:
    def inspect_sheets(self, file_path: str) -> List[str]:
        return ["Sheet1"]

    def read_sheet(self, file_path: str, sheet_name: str) -> List[Dict[str, Any]]:
        return []
