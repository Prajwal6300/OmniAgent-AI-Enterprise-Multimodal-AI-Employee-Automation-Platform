"""
OmniAgent AI — Database Agent Integration & API Tests
Verifies FastAPI endpoint POST /api/v1/agents/database/query, authentication enforcement,
Supervisor-to-Database Agent routing, and response envelope contracts.
"""

import uuid
from unittest.mock import AsyncMock, patch
import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.main import app
from app.models.user import User


class DummyAsyncSession:
    """Mock session for API integration tests."""
    def __init__(self):
        self.executed_statements = []

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

    async def execute(self, stmt, params=None):
        self.executed_statements.append(str(stmt))
        class DummyResult:
            returns_rows = True
            def keys(self):
                return ["pending_orders_count"]
            def all(self):
                return [(5,)]
        return DummyResult()


@pytest.fixture
def mock_authenticated_user():
    return User(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        email="db_tester@enterprise.omniagent.ai",
        full_name="Database Test User",
        is_active=True,
        is_verified=True,
        role_id=uuid.uuid4()
    )


# ==============================================================================
# 1. Authentication Guardrail Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_database_query_api_unauthorized():
    """Security: Verifies that unauthenticated calls to POST /api/v1/agents/database/query return 401."""
    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"question": "How many orders are pending?"}
        res = await client.post("/api/v1/agents/database/query", json=payload)
        assert res.status_code == 401


# ==============================================================================
# 2. Authenticated Query API Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_database_query_api_authenticated(mock_authenticated_user):
    """Verifies that authenticated requests execute successfully and return structured envelope."""
    async def mock_db():
        yield DummyAsyncSession()

    app.dependency_overrides[get_current_user] = lambda: mock_authenticated_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "question": "How many pending orders do we have?",
            "limit": 20
        }
        res = await client.post("/api/v1/agents/database/query", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "data" in data
        db_res = data["data"]
        assert db_res["question"] == payload["question"]
        assert "summary" in db_res
        assert "columns" in db_res
        assert "rows" in db_res
        assert db_res["query_executed"] is True
        assert db_res["confidence"] >= 0.90

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_database_query_api_empty_question_rejected(mock_authenticated_user):
    """Validation: Empty questions are rejected."""
    async def mock_db():
        yield DummyAsyncSession()

    app.dependency_overrides[get_current_user] = lambda: mock_authenticated_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"question": ""}
        res = await client.post("/api/v1/agents/database/query", json=payload)
        assert res.status_code == 422  # Pydantic min_length=1 validation error

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_database_query_api_unsupported_data(mock_authenticated_user):
    """Unsupported data inquiry returns controlled safe refusal."""
    async def mock_db():
        yield DummyAsyncSession()

    app.dependency_overrides[get_current_user] = lambda: mock_authenticated_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"question": "What is the secret cryptocurrency key for the company?"}
        res = await client.post("/api/v1/agents/database/query", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["query_executed"] is False
        assert "The requested information is not available in the authorized business data." in data["data"]["summary"]

    app.dependency_overrides.clear()


# ==============================================================================
# 3. Supervisor to Database Agent Routing Test
# ==============================================================================

@pytest.mark.asyncio
async def test_supervisor_routes_to_database_agent(mock_authenticated_user):
    """
    Supervisor Integration Test:
    User asks: 'Show all failed inspections this week.'
    Supervisor classifies: task_type='DATABASE_QUERY', selected_agent='database_agent'.
    """
    async def mock_db():
        yield DummyAsyncSession()

    app.dependency_overrides[get_current_user] = lambda: mock_authenticated_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"message": "Show all failed inspections this week."}
        res = await client.post("/api/v1/agents/supervisor/analyze", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        decision = data["data"]
        assert decision["task_type"] == "DATABASE_QUERY"
        assert decision["selected_agent"] == "database_agent"
        assert decision["confidence"] >= 0.90
        assert decision["requires_approval"] is False

    app.dependency_overrides.clear()
