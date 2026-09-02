from fastapi import APIRouter, Depends
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.user import UserRead
from app.schemas.common import ResponseEnvelope

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=ResponseEnvelope[UserRead])
async def get_me(current_user: User = Depends(get_current_user)):
    return ResponseEnvelope(data=current_user)
