from typing import Any


class ExcelProcessor:
    def inspect_sheets(self, file_path: str) -> list[str]:
        return ["Sheet1"]

    def read_sheet(self, file_path: str, sheet_name: str) -> list[dict[str, Any]]:
        return []
