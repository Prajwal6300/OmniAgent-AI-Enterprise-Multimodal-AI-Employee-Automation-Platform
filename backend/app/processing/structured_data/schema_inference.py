from typing import Any


class SchemaInference:
    def infer_columns(self, sample_records: list[dict[str, Any]]) -> dict[str, str]:
        schema = {}
        if not sample_records:
            return schema
        for key, val in sample_records[0].items():
            schema[key] = type(val).__name__
        return schema
