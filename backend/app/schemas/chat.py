from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MessageCreate(BaseModel):
    content: str
    agent_type: str | None = "SUPERVISOR"

class Citation(BaseModel):
    document_id: UUID
    document_name: str
    page_number: int | None = None
    chunk_index: int
    text_snippet: str

class MessageRead(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_type: str
    content: str
    citations: list[Citation] | None = None
    metadata: dict | None = None
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
