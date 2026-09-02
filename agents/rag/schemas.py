from typing import List
from pydantic import BaseModel

class RAGQuery(BaseModel):
    query: str
    top_k: int = 5

class RAGResponse(BaseModel):
    passages: List[str]
    sources: List[str]
