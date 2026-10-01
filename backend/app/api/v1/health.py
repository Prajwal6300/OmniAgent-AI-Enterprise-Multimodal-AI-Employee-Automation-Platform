"""
OmniAgent AI — Health & Deep Readiness Probes
Provides liveness (/health) and deep readiness (/ready) checking database,
pgvector extension, Redis connection, and storage availability.
"""

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis_client
from app.dependencies.database import get_db_session
from app.tools.storage.client import StorageClient

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Liveness probe for load balancers."""
    return {"status": "healthy", "service": "omniagent-backend"}


@router.get("/ready")
async def readiness_check(
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Deep readiness probe: verifies database, pgvector extension, Redis connectivity,
    and storage read/write capabilities before routing user traffic.
    """
    checks: dict[str, str] = {}
    is_ready = True

    # 1. Database Liveness & Vector Extension Check
    try:
        db_res = await session.execute(text("SELECT 1"))
        if db_res.scalar() == 1:
            checks["database"] = "ok"
        else:
            checks["database"] = "unexpected_response"
            is_ready = False
    except Exception as exc:  # noqa: BLE001
        logger.error("readiness_db_failed", error=str(exc))
        checks["database"] = f"error: {exc}"
        is_ready = False

    # Check pgvector extension
    try:
        ext_res = await session.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        )
        if ext_res.scalar_one_or_none() == "vector":
            checks["pgvector"] = "ok"
        else:
            checks["pgvector"] = "extension_missing_or_unregistered"
    except Exception as exc:  # noqa: BLE001
        checks["pgvector"] = f"check_failed: {exc}"

    # 2. Redis Connectivity Check
    try:
        redis_client = get_redis_client()
        await redis_client.set("health:ready_probe", "1", ex=10)
        val = await redis_client.get("health:ready_probe")
        if val == "1":
            checks["redis"] = "ok"
        else:
            checks["redis"] = "read_mismatch"
            is_ready = False
    except Exception as exc:  # noqa: BLE001
        logger.error("readiness_redis_failed", error=str(exc))
        checks["redis"] = f"error: {exc}"
        is_ready = False

    # 3. Storage Layer Check
    try:
        storage = StorageClient()
        probe_key = "system/health_probe.txt"
        await storage.upload("system_probe", probe_key, b"ok")
        data = await storage.download("system_probe", probe_key)
        await storage.delete("system_probe", probe_key)
        if data == b"ok":
            checks["storage"] = "ok"
        else:
            checks["storage"] = "data_mismatch"
            is_ready = False
    except Exception as exc:  # noqa: BLE001
        logger.error("readiness_storage_failed", error=str(exc))
        checks["storage"] = f"error: {exc}"
        is_ready = False

    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    response_payload = {
        "status": "ready" if is_ready else "unhealthy",
        "service": "omniagent-backend",
        "checks": checks,
    }

    if not is_ready:
        raise HTTPException(status_code=status_code, detail=response_payload)

    return response_payload
