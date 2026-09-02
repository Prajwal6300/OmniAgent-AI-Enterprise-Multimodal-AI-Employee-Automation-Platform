from typing import List, Dict, Any
from pydantic import BaseModel

class DocumentExtractionResult(BaseModel):
    document_id: str
    tables: List[Dict[str, Any]] = []
    key_value_pairs: Dict[str, str] = {}
