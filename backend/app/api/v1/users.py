from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=ResponseEnvelope[UserRead])
async def get_me(current_user: User = Depends(get_current_user)):
    return ResponseEnvelope(data=current_user)
