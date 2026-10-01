from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    trigger_type: str = Field(default="MANUAL")
    trigger_config: dict[str, Any] = Field(default_factory=dict)
    graph_definition: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    trigger_type: str | None = None
    trigger_config: dict[str, Any] | None = None
    graph_definition: dict[str, Any] | None = None
    is_active: bool | None = None


class WorkflowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    description: str | None = None
    trigger_type: str
    trigger_config: dict[str, Any] = Field(default_factory=dict)
    graph_definition: dict[str, Any] = Field(default_factory=dict)
    is_active: bool
    created_at: datetime
    updated_at: datetime


class WorkflowRunCreate(BaseModel):
    input_payload: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    organization_id: UUID
    status: str
    current_step: str | None = None
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] | None = None
    started_at: datetime
    finished_at: datetime | None = None
    error_details: str | None = None
