from typing import Optional, List
from pydantic import BaseModel

class SupervisorDecision(BaseModel):
    next_agent: str
    reasoning: str
    is_task_complete: bool = False
    directives: Optional[List[str]] = None
