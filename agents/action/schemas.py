from typing import Dict, Any
from pydantic import BaseModel

class ActionProposal(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    risk_level: str # LOW, MEDIUM, HIGH
    requires_approval: bool
