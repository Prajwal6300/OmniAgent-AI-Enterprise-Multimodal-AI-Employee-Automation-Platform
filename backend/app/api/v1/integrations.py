from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.common import ResponseEnvelope

router = APIRouter(prefix="/integrations", tags=["Integrations"])

@router.get("")
async def list_integrations(current_user: User = Depends(get_current_user)):
    return ResponseEnvelope(data=[])
