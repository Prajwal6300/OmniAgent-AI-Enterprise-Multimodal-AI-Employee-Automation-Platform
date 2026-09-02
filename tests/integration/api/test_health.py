import pytest
from backend.app.api.v1.health import health_check

@pytest.mark.asyncio
async def test_health_endpoint():
    res = await health_check()
    assert res["status"] == "healthy"
