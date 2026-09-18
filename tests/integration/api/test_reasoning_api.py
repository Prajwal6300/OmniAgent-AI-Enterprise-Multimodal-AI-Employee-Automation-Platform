"""
OmniAgent AI — Reasoning Agent Integration & API Tests
Verifies FastAPI endpoint POST /api/v1/agents/reasoning/analyze,
authentication enforcement, tenant isolation, cross-tenant artifact rejection,
Supervisor cognitive routing to reasoning agent, and response envelope contracts.
"""

import uuid

import pytest
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.main import app
from app.models.user import User
from httpx import ASGITransport, AsyncClient


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
                return ["id", "machine_id", "status"]

            def all(self):
                return [(1, "M-102", "operational")]

            def fetchall(self):
                return [(1, "M-102", "operational")]

            def scalar_one_or_none(self):
                return None

            def scalars(self):
                class DummyScalars:
                    def all(self):
                        return []

                return DummyScalars()

        return DummyResult()


@pytest.fixture
def mock_authenticated_user():
    return User(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        email="reasoning_tester@enterprise.omniagent.ai",
        full_name="Reasoning Test User",
        is_active=True,
        is_verified=True,
        role_id=uuid.uuid4(),
    )


@pytest.mark.asyncio
async def test_reasoning_api_unauthenticated():
    """Verify that calling the endpoint without credentials returns 401 Unauthorized."""
    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/agents/reasoning/analyze",
            json={"question": "Compare this machine with maintenance records."},
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_reasoning_api_authenticated_valid(mock_authenticated_user):
    """
    Verify authenticated call executes multi-source analysis and returns 200
    with valid ResponseEnvelope containing answer, evidence, and task type.
    """

    async def mock_db():
        yield DummyAsyncSession()

    app.dependency_overrides[get_current_user] = lambda: mock_authenticated_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "question": "Compare this inspection image with the maintenance records and explain the likely issue.",
            "conversation_id": str(uuid.uuid4()),
        }
        res = await client.post("/api/v1/agents/reasoning/analyze", json=payload)

        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        data = body["data"]

        assert "answer" in data
        assert data["task_type"] == "IMAGE_DATABASE_ANALYSIS"
        assert "evidence" in data
        assert data["grounded"] is True
        assert data["confidence"] > 0.0
        assert data["requires_approval"] is False

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_reasoning_api_invalid_request_empty_question(mock_authenticated_user):
    """Verify request with empty question returns 422 Unprocessable Entity."""

    async def mock_db():
        yield DummyAsyncSession()

    app.dependency_overrides[get_current_user] = lambda: mock_authenticated_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"question": ""}
        res = await client.post("/api/v1/agents/reasoning/analyze", json=payload)
        assert res.status_code == 422

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_reasoning_api_tenant_isolation_cross_tenant_image(
    mock_authenticated_user,
):
    """
    Verify providing an image ID that does not belong to the user's organization
    is rejected with 404 Not Found.
    """

    async def mock_db():
        yield DummyAsyncSession()

    app.dependency_overrides[get_current_user] = lambda: mock_authenticated_user
    app.dependency_overrides[get_db_session] = mock_db

    foreign_image_id = str(uuid.uuid4())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "question": "Compare this image with maintenance records.",
            "image_id": foreign_image_id,
        }
        res = await client.post("/api/v1/agents/reasoning/analyze", json=payload)
        assert res.status_code == 404
        assert "not found in this organization" in res.json()["detail"].lower()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_reasoning_api_tenant_isolation_cross_tenant_document(
    mock_authenticated_user,
):
    """
    Verify providing a document ID that does not belong to the user's organization
    is rejected with 404 Not Found.
    """

    async def mock_db():
        yield DummyAsyncSession()

    app.dependency_overrides[get_current_user] = lambda: mock_authenticated_user
    app.dependency_overrides[get_db_session] = mock_db

    foreign_doc_id = str(uuid.uuid4())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "question": "Read the maintenance manual and check procedures.",
            "document_id": foreign_doc_id,
        }
        res = await client.post("/api/v1/agents/reasoning/analyze", json=payload)
        assert res.status_code == 404
        assert "not found in this organization" in res.json()["detail"].lower()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_supervisor_routes_to_reasoning_agent(mock_authenticated_user):
    """
    Verify Supervisor Agent routing classifies multi-source query and selects reasoning_agent.
    """

    async def mock_db():
        yield DummyAsyncSession()

    app.dependency_overrides[get_current_user] = lambda: mock_authenticated_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "message": "Compare this inspection image with the maintenance records and explain the likely issue.",
        }
        res = await client.post("/api/v1/agents/supervisor/analyze", json=payload)

        assert res.status_code == 200
        decision = res.json()["data"]
        assert decision["selected_agent"] == "reasoning_agent"
        assert decision["task_type"] == "DATA_ANALYSIS"
        assert decision["requires_approval"] is False

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_reasoning_api_no_internal_cot_exposed(mock_authenticated_user):
    """
    Verify response answer does NOT expose internal chain-of-thought traces.
    """

    async def mock_db():
        yield DummyAsyncSession()

    app.dependency_overrides[get_current_user] = lambda: mock_authenticated_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "question": "Analyze this month's production failures and summarize the most common causes.",
        }
        res = await client.post("/api/v1/agents/reasoning/analyze", json=payload)

        assert res.status_code == 200
        answer = res.json()["data"]["answer"]

        # Ensure no internal scratchpad or CoT patterns
        assert "Step 1: I thought" not in answer
        assert "Step 2: I considered" not in answer
        assert "internal reasoning" not in answer.lower()

    app.dependency_overrides.clear()
