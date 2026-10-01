"""
OmniAgent AI — Integration Schemas
Defines request and response contracts for tenant integrations with secret redaction.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IntegrationCreate(BaseModel):
    service_name: str = Field(..., min_length=2, max_length=100)
    is_enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class IntegrationUpdate(BaseModel):
    is_enabled: bool | None = None
    config: dict[str, Any] | None = None


class IntegrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    service_name: str
    is_enabled: bool
    config: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class IntegrationTestResult(BaseModel):
    success: bool
    message: str
    latency_ms: int
