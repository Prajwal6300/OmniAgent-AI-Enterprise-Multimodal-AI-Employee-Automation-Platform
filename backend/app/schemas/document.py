from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any
from pydantic import BaseModel

class DocumentRead(BaseModel):
    id: UUID
    organization_id: UUID
    file_name: str
    file_type: str
    file_size_bytes: int
    processing_status: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
