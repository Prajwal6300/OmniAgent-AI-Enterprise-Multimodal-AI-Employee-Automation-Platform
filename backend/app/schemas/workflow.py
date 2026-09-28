from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    trigger_type: str = Field(default="MANUAL")
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    graph_definition: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    graph_definition: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class WorkflowRead(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    description: Optional[str] = None
    trigger_type: str
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    graph_definition: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowRunCreate(BaseModel):
    input_payload: Dict[str, Any] = Field(default_factory=dict)


class WorkflowRunRead(BaseModel):
    id: UUID
    workflow_id: UUID
    organization_id: UUID
    status: str
    current_step: Optional[str] = None
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    output_payload: Optional[Dict[str, Any]] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    error_details: Optional[str] = None

    class Config:
        from_attributes = True
