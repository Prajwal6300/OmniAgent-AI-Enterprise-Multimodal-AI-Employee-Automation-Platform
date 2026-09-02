from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db_session
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest, Token
from app.schemas.common import ResponseEnvelope

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=ResponseEnvelope[Token])
async def login(request: LoginRequest, session: AsyncSession = Depends(get_db_session)):
    service = AuthService(session)
    token = await service.authenticate(request)
    return ResponseEnvelope(data=token, message="Authentication successful")
