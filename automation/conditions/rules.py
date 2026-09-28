from typing import Any
from pydantic import BaseModel, Field, model_validator


class Rule(BaseModel):
    field: str
    operator: str
    expected_value: Any = None
    value: Any = None

    @model_validator(mode="after")
    def sync_values(self) -> "Rule":
        if self.expected_value is None and self.value is not None:
            self.expected_value = self.value
        elif self.value is None and self.expected_value is not None:
            self.value = self.expected_value
        return self
