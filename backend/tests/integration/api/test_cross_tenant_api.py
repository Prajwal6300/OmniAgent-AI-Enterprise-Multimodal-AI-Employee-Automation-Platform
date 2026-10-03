"""
OmniAgent AI — API Cross-Tenant Isolation Tests

Validates that Tenant A tokens cannot access Tenant B resources via API endpoints.
Expected behavior: 403 Forbidden or 404 Not Found when requesting cross-tenant resources.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.main import app
from app.models.document import Document
from app.models.user import User


class CrossTenantSession:
    """In-memory async session supporting multi-tenant document queries."""

    def __init__(self, documents: dict[uuid.UUID, Document]):
        self.documents = documents

    async def execute(self, stmt):
        try:
            params = stmt.compile().params
        except SQLAlchemyError:  # stmt.compile() may raise if dialect/params incompatible; fall back to empty params
            params = {}

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

        target_doc_id = None
        target_org_id = None
        for k, v in params.items():
            if "id" in k and "org" not in k and isinstance(v, uuid.UUID):
                target_doc_id = v
            elif "org" in k and isinstance(v, uuid.UUID):
                target_org_id = v

        matched = []
        for doc in self.documents.values():
            if target_doc_id is not None and doc.id != target_doc_id:
                continue
            if target_org_id is not None and doc.organization_id != target_org_id:
                continue
            matched.append(doc)

        return Result(matched)

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_cross_tenant_document_access_403_or_404():
    """Tenant B authenticated user requesting Tenant A document => 404 Not Found."""
    org_a_id = uuid.uuid4()
    org_b_id = uuid.uuid4()

    user_b = User(
        id=uuid.uuid4(),
        organization_id=org_b_id,
        email="b@beta.com",
        full_name="User B",
        hashed_password="hash",
        role_id=uuid.uuid4(),
    )

    doc_a = Document(
        id=uuid.uuid4(),
        organization_id=org_a_id,
        file_name="alpha.pdf",
        file_path="/storage/alpha.pdf",
        file_type="application/pdf",
        file_size_bytes=1024,
        checksum_sha256="a" * 64,
        processing_status="PROCESSED",
    )
    doc_b = Document(
        id=uuid.uuid4(),
        organization_id=org_b_id,
        file_name="beta.pdf",
        file_path="/storage/beta.pdf",
        file_type="application/pdf",
        file_size_bytes=2048,
        checksum_sha256="b" * 64,
        processing_status="PROCESSED",
    )

    docs = {doc_a.id: doc_a, doc_b.id: doc_b}
    mock_session = CrossTenantSession(docs)

    async def mock_db():
        yield mock_session

    app.dependency_overrides[get_db_session] = mock_db
    app.dependency_overrides[get_current_user] = lambda: user_b

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Tenant B tries to access Tenant A's document => 404 (isolated)
            res = await client.get(f"/api/v1/documents/{doc_a.id}")
            assert res.status_code in (403, 404), f"Expected 403/404, got {res.status_code}"

            # Tenant B accesses Tenant B's own document => 200 OK
            res_own = await client.get(f"/api/v1/documents/{doc_b.id}")
            assert res_own.status_code == 200
    finally:
        app.dependency_overrides.clear()