from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any
from pydantic import BaseModel

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str
    trigger_config: Dict[str, Any]
    graph_definition: Dict[str, Any]

class WorkflowRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    trigger_type: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
