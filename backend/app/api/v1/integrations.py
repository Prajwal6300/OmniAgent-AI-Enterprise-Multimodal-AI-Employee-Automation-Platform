"""
OmniAgent AI — Integrations API Endpoints
Provides full tenant-isolated CRUD for encrypted integrations, secret redaction, and test-connection.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.schemas.integration import (
    IntegrationCreate,
    IntegrationRead,
    IntegrationTestResult,
    IntegrationUpdate,
)
from app.services.integration_service import IntegrationService

router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.get("", response_model=ResponseEnvelope[list[IntegrationRead]])
async def list_integrations(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = IntegrationService(session)
    data = await service.list_integrations(current_user.organization_id)
    return ResponseEnvelope(data=data)


@router.post("", response_model=ResponseEnvelope[IntegrationRead], status_code=status.HTTP_201_CREATED)
async def create_integration(
    payload: IntegrationCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = IntegrationService(session)
    data = await service.create_integration(current_user.organization_id, payload)
    return ResponseEnvelope(data=data, message="Integration configured successfully")


@router.get("/{integration_id}", response_model=ResponseEnvelope[IntegrationRead])
async def get_integration(
    integration_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = IntegrationService(session)
    try:
        data = await service.get_integration(integration_id, current_user.organization_id)
        return ResponseEnvelope(data=data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{integration_id}", response_model=ResponseEnvelope[IntegrationRead])
async def update_integration(
    integration_id: UUID,
    payload: IntegrationUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = IntegrationService(session)
    try:
        data = await service.update_integration(integration_id, current_user.organization_id, payload)
        return ResponseEnvelope(data=data, message="Integration updated successfully")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{integration_id}", response_model=ResponseEnvelope[dict])
async def delete_integration(
    integration_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = IntegrationService(session)
    try:
        await service.delete_integration(integration_id, current_user.organization_id)
        return ResponseEnvelope(data={"deleted": True}, message="Integration removed")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{integration_id}/test", response_model=ResponseEnvelope[IntegrationTestResult])
async def test_integration_connection(
    integration_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = IntegrationService(session)
    try:
        result = await service.test_connection(integration_id, current_user.organization_id)
        return ResponseEnvelope(data=result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
