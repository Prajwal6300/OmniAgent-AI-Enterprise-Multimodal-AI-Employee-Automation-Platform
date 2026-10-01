import csv
from typing import Any


class CSVProcessor:
    def read_records(self, file_path: str, limit: int = 100) -> list[dict[str, Any]]:
        records = []
        try:
            with open(file_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    if idx >= limit:
                        break
                    records.append(row)
        except (OSError, UnicodeDecodeError, csv.Error):
            return records
        return records
