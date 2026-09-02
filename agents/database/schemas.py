from typing import Optional, List
from pydantic import BaseModel

class GeneratedQuery(BaseModel):
    sql: str
    parameters: dict = {}
    is_safe: bool = True
    explanation: str
