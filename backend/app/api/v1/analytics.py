from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.common import ResponseEnvelope

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/overview")
async def get_analytics_overview(current_user: User = Depends(get_current_user)):
    return ResponseEnvelope(data={"total_runs": 0, "total_cost_usd": 0.0, "pending_approvals": 0})
