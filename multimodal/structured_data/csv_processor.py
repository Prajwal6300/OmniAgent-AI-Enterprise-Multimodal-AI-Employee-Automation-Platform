import csv
from typing import List, Dict, Any

class CSVProcessor:
    def read_records(self, file_path: str, limit: int = 100) -> List[Dict[str, Any]]:
        records = []
        try:
            with open(file_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    if idx >= limit:
                        break
                    records.append(row)
        except Exception:
            pass
        return records
