from datetime import datetime
from uuid import UUID
from typing import Optional, List, Any
from pydantic import BaseModel

class MessageCreate(BaseModel):
    content: str
    agent_type: Optional[str] = "SUPERVISOR"

class Citation(BaseModel):
    document_id: UUID
    document_name: str
    page_number: Optional[int] = None
    chunk_index: int
    text_snippet: str

class MessageRead(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_type: str
    content: str
    citations: Optional[List[Citation]] = None
    metadata: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationRead(BaseModel):
    id: UUID
    title: str
    agent_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
