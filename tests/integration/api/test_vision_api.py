"""
Integration Tests for Vision Agent API Endpoints.
Verifies authentication, tenant boundary isolation, multipart file uploads,
analysis execution, and cross-tenant access prevention.
"""

import io
import uuid

import pytest
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.main import app
from app.models.document import Document
from app.models.user import User
from httpx import ASGITransport, AsyncClient
from PIL import Image


class InMemoryAsyncSession:
    """In-memory async session tracking Document objects."""

    def __init__(self):
        self.documents: dict[uuid.UUID, Document] = {}

    def add(self, obj):
        if hasattr(obj, "id"):
            if not obj.id:
                obj.id = uuid.uuid4()
            self.documents[obj.id] = obj

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def close(self):
        pass

    async def execute(self, stmt):
        compiled = stmt.compile()
        params = getattr(compiled, "params", {}) or {}

        target_id = None
        target_org = None
        for k, v in params.items():
            if k.startswith("id"):
                target_id = str(v)
            elif k.startswith("organization_id"):
                target_org = str(v)

        docs = list(self.documents.values())
        matched = []
        for d in docs:
            if target_id is not None and str(d.id) != target_id:
                continue
            if target_org is not None and str(d.organization_id) != target_org:
                continue
            matched.append(d)

        class Result:
            def __init__(self, data):
                self._data = data

            def scalar_one_or_none(self):
                return self._data[0] if self._data else None

            def scalars(self):
                class Scalars:
                    def __init__(self, d):
                        self._d = d

                    def all(self):
                        return self._d

                return Scalars(self._data)

        return Result(matched)


@pytest.fixture
def mock_user_org_a():
    return User(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        email="org_a_user@enterprise.omniagent.ai",
        full_name="Org A Analyst",
        is_active=True,
        is_verified=True,
        role_id=uuid.uuid4(),
    )


@pytest.fixture
def mock_user_org_b():
    return User(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        email="org_b_user@enterprise.omniagent.ai",
        full_name="Org B Analyst",
        is_active=True,
        is_verified=True,
        role_id=uuid.uuid4(),
    )


def make_test_jpeg(size=(200, 200), color="blue") -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_vision_upload_unauthorized():
    """Security Test: POST /api/v1/agents/vision/upload without auth returns 401."""
    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("image.jpg", b"fake", "image/jpeg")}
        res = await client.post("/api/v1/agents/vision/upload", files=files)
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_vision_upload_authenticated(mock_user_org_a):
    """Integration Test: POST /api/v1/agents/vision/upload persists image."""
    shared_session = InMemoryAsyncSession()

    async def mock_db():
        yield shared_session

    app.dependency_overrides[get_current_user] = lambda: mock_user_org_a
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        img_bytes = make_test_jpeg()
        files = {"file": ("inspection_photo.jpg", img_bytes, "image/jpeg")}
        res = await client.post("/api/v1/agents/vision/upload", files=files)

        assert res.status_code == 201
        payload = res.json()
        assert payload["success"] is True
        assert payload["data"]["file_name"] == "inspection_photo.jpg"
        assert payload["data"]["width"] == 200
        assert payload["data"]["height"] == 200


@pytest.mark.asyncio
async def test_vision_upload_unsupported_format(mock_user_org_a):
    """Validation Test: Uploading non-image file is rejected with 400."""
    shared_session = InMemoryAsyncSession()

    async def mock_db():
        yield shared_session

    app.dependency_overrides[get_current_user] = lambda: mock_user_org_a
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("script.py", b"print('hack')", "text/x-python")}
        res = await client.post("/api/v1/agents/vision/upload", files=files)

        assert res.status_code == 400
        assert "unsupported" in res.text.lower()


@pytest.mark.asyncio
async def test_vision_analyze_authenticated(mock_user_org_a):
    """Integration Test: POST /api/v1/agents/vision/analyze executes LangGraph vision pipeline."""
    shared_session = InMemoryAsyncSession()

    async def mock_db():
        yield shared_session

    app.dependency_overrides[get_current_user] = lambda: mock_user_org_a
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload valid image first
        img_bytes = make_test_jpeg()
        files = {"file": ("machine_test.jpg", img_bytes, "image/jpeg")}
        upload_res = await client.post("/api/v1/agents/vision/upload", files=files)
        assert upload_res.status_code == 201
        image_id = upload_res.json()["data"]["id"]

        # 2. Analyze the uploaded image
        analyze_payload = {
            "image_id": image_id,
            "question": "Inspect this machine for visible defects or wear.",
            "task_type": "VISUAL_INSPECTION",
        }
        res = await client.post("/api/v1/agents/vision/analyze", json=analyze_payload)

        assert res.status_code == 200
        data = res.json()["data"]
        assert data["image_id"] == image_id
        assert data["task_type"] == "VISUAL_INSPECTION"
        assert data["confidence"] > 0.0
        assert len(data["findings"]) >= 1


@pytest.mark.asyncio
async def test_vision_cross_tenant_isolation(mock_user_org_a, mock_user_org_b):
    """Security Test: Tenant B user cannot analyze or access Tenant A's image."""
    shared_session = InMemoryAsyncSession()

    async def mock_db():
        yield shared_session

    # Step 1: Upload as Org A
    app.dependency_overrides[get_current_user] = lambda: mock_user_org_a
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        img_bytes = make_test_jpeg()
        files = {"file": ("org_a_secret_machine.jpg", img_bytes, "image/jpeg")}
        upload_res = await client.post("/api/v1/agents/vision/upload", files=files)
        image_id = upload_res.json()["data"]["id"]

    # Step 2: Attempt analysis as Org B -> Must be rejected with 404
    app.dependency_overrides[get_current_user] = lambda: mock_user_org_b

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/agents/vision/analyze",
            json={"image_id": image_id, "question": "What is in Org A's machine?"},
        )
        assert res.status_code == 404
        assert "not found in this organization" in res.json()["detail"].lower()
