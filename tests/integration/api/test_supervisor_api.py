import uuid

import pytest
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.main import app
from app.models.user import User
from httpx import ASGITransport, AsyncClient


class DummyAsyncSession:
    async def flush(self):
        pass
    def add(self, obj):
        pass
    async def commit(self):
        pass
    async def rollback(self):
        pass
    async def close(self):
        pass


@pytest.fixture
def mock_authenticated_user():
    user = User(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        email="supervisor_tester@enterprise.omniagent.ai",
        full_name="Supervisor Test Agent",
        is_active=True,
        is_verified=True,
        role_id=uuid.uuid4()
    )
    return user


@pytest.mark.asyncio
async def test_supervisor_analyze_api_authenticated(mock_authenticated_user):
    """
    Tests POST /api/v1/agents/supervisor/analyze with valid authenticated session.
    Verifies that the trusted organization and user IDs are utilized.
    """
    async def mock_db():
        yield DummyAsyncSession()

    app.dependency_overrides[get_current_user] = lambda: mock_authenticated_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "message": "Summarize this quarterly financial PDF and check invoices",
            "conversation_id": str(uuid.uuid4()),
            "context": {"department": "finance"}
        }
        res = await client.post("/api/v1/agents/supervisor/analyze", json=payload)
        
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        decision = data["data"]
        assert decision["task_type"] == "DOCUMENT_ANALYSIS"
        assert decision["selected_agent"] == "document_agent"
        assert decision["confidence"] >= 0.90
        assert decision["requires_approval"] is False
        assert len(decision["task_plan"]) > 0

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_supervisor_analyze_api_unauthorized():
    """
    Security Test: Verifies that unauthenticated calls are rejected with 401.
    """
    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "message": "Find company policy on vacation days"
        }
        res = await client.post("/api/v1/agents/supervisor/analyze", json=payload)
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_supervisor_analyze_destructive_action_api(mock_authenticated_user):
    """
    Tests POST /api/v1/agents/supervisor/analyze with high risk request.
    Verifies requires_approval=True and priority=high are returned in API envelope.
    """
    async def mock_db():
        yield DummyAsyncSession()

    app.dependency_overrides[get_current_user] = lambda: mock_authenticated_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "message": "Delete the employee record for user 9021"
        }
        res = await client.post("/api/v1/agents/supervisor/analyze", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        decision = data["data"]
        assert decision["priority"] == "high"
        assert decision["requires_approval"] is True
        assert decision["requires_tool"] is True

    app.dependency_overrides.clear()
