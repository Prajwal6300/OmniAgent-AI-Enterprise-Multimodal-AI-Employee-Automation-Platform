from typing import Any

from pydantic import BaseModel


class ToolExecutionRequest(BaseModel):
    tool_name: str
    user_id: str
    organization_id: str
    parameters: dict[str, Any]

class ToolExecutionResult(BaseModel):
    success: bool
    data: Any | None = None
    error: str | None = None
