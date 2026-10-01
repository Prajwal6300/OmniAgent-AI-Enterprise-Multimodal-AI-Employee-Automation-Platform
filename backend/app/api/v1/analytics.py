"""
OmniAgent AI — Analytics API Endpoints
Provides real tenant-scoped analytics overview, token usage, cost breakdowns, and p50/p95/p99 latency.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
async def get_analytics_overview(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = AnalyticsService(session)
    data = await service.get_overview(current_user.organization_id, days=days)
    return ResponseEnvelope(data=data)
