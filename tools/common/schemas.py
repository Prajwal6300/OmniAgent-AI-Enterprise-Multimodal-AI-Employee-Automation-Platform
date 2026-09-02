from typing import Dict, Any, Optional
from pydantic import BaseModel

class ToolExecutionRequest(BaseModel):
    tool_name: str
    user_id: str
    organization_id: str
    parameters: Dict[str, Any]

class ToolExecutionResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
