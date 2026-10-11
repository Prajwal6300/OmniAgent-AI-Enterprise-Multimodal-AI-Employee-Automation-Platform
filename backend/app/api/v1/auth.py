"""
OmniAgent AI — Authentication API Endpoints
Provides login, tenant bootstrap registration, token refresh with rotation, and logout.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.dependencies.database import get_db_session
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RegisterRequest,
    Token,
)
from app.schemas.common import ResponseEnvelope
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=ResponseEnvelope[Token])
async def login(
    request: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
):
    service = AuthService(session)
    try:
        token = await service.authenticate(request)
        # Set refresh token as HttpOnly Secure SameSite cookie
        response.set_cookie(
            key="refresh_token",
            value=token.refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            path="/auth/refresh",
            max_age=7 * 24 * 60 * 60,  # 7 days
        )
        return ResponseEnvelope(data=Token(access_token=token.access_token), message="Authentication successful")
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
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Refresh token read from HttpOnly cookie set on login."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token cookie not found")

    service = AuthService(session)
    try:
        token = await service.refresh(refresh_token)
        # Set new refresh token cookie
        response = Response(
            content={"access_token": token.access_token, "refresh_token": token.refresh_token},
            status_code=200,
        )
        response.set_cookie(
            key="refresh_token",
            value=token.refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            path="/auth/refresh",
            max_age=7 * 24 * 60 * 60,
        )
        return response
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/logout", response_model=ResponseEnvelope[dict])
async def logout(
    request: LogoutRequest,
    session: AsyncSession = Depends(get_db_session),
    response: Response = Response(),
):
    service = AuthService(session)
    await service.logout(response.cookies.get("refresh_token"))
    response.set_cookie(
        key="refresh_token",
        value="",
        httponly=True,
        secure=True,
        samesite="strict",
        path="/auth/refresh",
        max_age=0,
    )
    return ResponseEnvelope(data={"logged_out": True}, message="Logged out successfully")