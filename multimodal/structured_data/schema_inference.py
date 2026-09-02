from typing import Dict, Any, List

class SchemaInference:
    def infer_columns(self, sample_records: List[Dict[str, Any]]) -> Dict[str, str]:
        schema = {}
        if not sample_records:
            return schema
        for key, val in sample_records[0].items():
            schema[key] = type(val).__name__
        return schema
