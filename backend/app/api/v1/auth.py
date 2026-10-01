"""
OmniAgent AI — Authentication API Endpoints
Provides login, tenant bootstrap registration, token refresh with rotation, and logout.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.dependencies.database import get_db_session
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    Token,
)
from app.schemas.common import ResponseEnvelope
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=ResponseEnvelope[Token])
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
):
    service = AuthService(session)
    try:
        token = await service.authenticate(request)
        return ResponseEnvelope(data=token, message="Authentication successful")
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/register", response_model=ResponseEnvelope[Token], status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
):
    service = AuthService(session)
    try:
        token = await service.register(request)
        return ResponseEnvelope(data=token, message="Organization and owner account created successfully")
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/refresh", response_model=ResponseEnvelope[Token])
async def refresh_token(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session),
):
    service = AuthService(session)
    try:
        token = await service.refresh(request.refresh_token)
        return ResponseEnvelope(data=token, message="Token refreshed successfully")
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/logout", response_model=ResponseEnvelope[dict])
async def logout(
    request: LogoutRequest,
    session: AsyncSession = Depends(get_db_session),
):
    service = AuthService(session)
    await service.logout(request.refresh_token)
    return ResponseEnvelope(data={"logged_out": True}, message="Logged out successfully")
