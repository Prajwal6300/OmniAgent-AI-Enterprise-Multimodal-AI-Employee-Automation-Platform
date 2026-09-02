from typing import Dict, Any, Optional
from pydantic import BaseModel

class WorkflowRunState(BaseModel):
    run_id: str
    workflow_id: str
    status: str # PENDING, RUNNING, PAUSED_FOR_APPROVAL, COMPLETED, FAILED
    context: Dict[str, Any] = {}
    current_node: Optional[str] = None
    error: Optional[str] = None
