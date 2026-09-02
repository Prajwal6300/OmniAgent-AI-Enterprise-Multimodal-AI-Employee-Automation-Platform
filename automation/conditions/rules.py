from pydantic import BaseModel
from typing import Any

class Rule(BaseModel):
    field: str
    operator: str
    expected_value: Any
