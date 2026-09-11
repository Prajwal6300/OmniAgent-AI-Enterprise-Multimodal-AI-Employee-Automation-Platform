import uuid
from unittest.mock import AsyncMock, patch

import pytest
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.main import app
from app.models.document import Document
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
    async def execute(self, stmt):
        class DummyResult:
            def all(self):
                return []
            def scalar_one_or_none(self):
                return None
            def scalars(self):
                class ScalarList:
                    def all(self):
                        return []
                return ScalarList()
        return DummyResult()


@pytest.fixture
def mock_authenticated_user():
    return User(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        email="rag_tester@enterprise.omniagent.ai",
        full_name="RAG Test User",
        is_active=True,
        is_verified=True,
        role_id=uuid.uuid4()
    )


@pytest.mark.asyncio
async def test_rag_query_api_unauthorized():
    """Security: Verifies that unauthenticated calls are rejected with 401."""
    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"question": "What is the leave policy?"}
        res = await client.post("/api/v1/agents/rag/query", json=payload)
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_rag_query_api_authenticated(mock_authenticated_user):
    """Tests POST /api/v1/agents/rag/query with valid authentication."""
    async def mock_db():
        yield DummyAsyncSession()

    app.dependency_overrides[get_current_user] = lambda: mock_authenticated_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "question": "What is the company leave policy?",
            "document_id": None
        }
        res = await client.post("/api/v1/agents/rag/query", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "answer" in data["data"]
        assert "grounded" in data["data"]
        assert "confidence" in data["data"]
        assert "citations" in data["data"]
        assert isinstance(data["data"]["citations"], list)
        assert "retrieved_chunks" in data["data"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rag_query_api_invalid_document_uuid(mock_authenticated_user):
    """Tests validation error on malformed document UUID string."""
    async def mock_db():
        yield DummyAsyncSession()

    app.dependency_overrides[get_current_user] = lambda: mock_authenticated_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "question": "What is the leave policy?",
            "document_id": "not-a-valid-uuid"
        }
        res = await client.post("/api/v1/agents/rag/query", json=payload)
        assert res.status_code == 400
        data = res.json()
        assert "detail" in data

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_document_indexing_endpoint(mock_authenticated_user):
    """Tests POST /api/v1/documents/{document_id}/index."""
    async def mock_db():
        yield DummyAsyncSession()

    app.dependency_overrides[get_current_user] = lambda: mock_authenticated_user
    app.dependency_overrides[get_db_session] = mock_db

    doc_id = uuid.uuid4()
    mock_doc = Document(
        id=doc_id,
        organization_id=mock_authenticated_user.organization_id,
        file_name="handbook.pdf",
        file_path="storage/documents/handbook.pdf",
        file_type="application/pdf",
        file_size_bytes=1024,
        checksum_sha256="dummychecksum",
        processing_status="PROCESSED",
        metadata_={"indexing_status": "NOT_INDEXED"}
    )

    with patch("app.services.document_service.DocumentRepository.get_by_id_and_org", return_value=mock_doc), \
         patch("app.services.rag.ingestion.pipeline.RAGIngestionPipeline.index_document", return_value=4):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(f"/api/v1/documents/{doc_id}/index")
            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            assert data["data"]["indexing_status"] == "INDEXED"
            assert data["data"]["chunks_indexed"] == 4

    app.dependency_overrides.clear()
