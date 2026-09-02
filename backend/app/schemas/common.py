from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel

T = TypeVar("T")

class ResponseEnvelope(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[dict] = None

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
