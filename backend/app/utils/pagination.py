from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class PageParams(BaseModel):
    page: int = 1
    size: int = 50

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
