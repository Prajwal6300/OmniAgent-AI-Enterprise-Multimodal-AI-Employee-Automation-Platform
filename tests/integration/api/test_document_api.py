import io
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from reportlab.pdfgen import canvas

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.main import app
from app.models.document import Document
from app.models.user import User


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
        # Extract where conditions
        stmt_str = str(stmt)
        docs = list(self.documents.values())

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

        # Basic query filtering for in-memory tests
        matched = []
        for d in docs:
            # Check if this doc matches the query
            matched.append(d)
        return Result(matched)


@pytest.fixture
def mock_user_org_a():
    return User(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        email="tenant_a@enterprise.omniagent.ai",
        full_name="Tenant A Admin",
        is_active=True,
        is_verified=True,
        role_id=uuid.uuid4()
    )


@pytest.fixture
def mock_user_org_b():
    return User(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        email="tenant_b@enterprise.omniagent.ai",
        full_name="Tenant B Admin",
        is_active=True,
        is_verified=True,
        role_id=uuid.uuid4()
    )


def make_test_pdf(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 750
    for line in text.split("\n"):
        c.drawString(100, y, line)
        y -= 20
    c.showPage()
    c.save()
    return buf.getvalue()


@pytest.mark.asyncio
async def test_document_upload_api_unauthorized():
    """Security Test: POST /api/v1/documents/upload without auth token returns 401."""
    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("test.txt", b"Hello", "text/plain")}
        res = await client.post("/api/v1/documents/upload", files=files)
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_document_upload_api_authenticated(mock_user_org_a):
    """Integration Test: POST /api/v1/documents/upload with valid session stores document."""
    shared_session = InMemoryAsyncSession()

    async def mock_db():
        yield shared_session

    app.dependency_overrides[get_current_user] = lambda: mock_user_org_a
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pdf_bytes = make_test_pdf("TAX INVOICE\nVendor: Acme Supplies\nTotal: $1,000.00")
        files = {"file": ("invoice_acme.pdf", pdf_bytes, "application/pdf")}
        res = await client.post("/api/v1/documents/upload", files=files)

        assert res.status_code == 201
        data = res.json()
        assert data["success"] is True
        doc_data = data["data"]
        assert doc_data["file_name"] == "invoice_acme.pdf"
        assert doc_data["processing_status"] == "UPLOADED"
        assert "id" in doc_data

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_document_upload_and_analyze_flow(mock_user_org_a):
    """
    End-to-End API Test:
    Upload document -> Verify status=UPLOADED -> Analyze document -> Verify structured response & PROCESSED.
    """
    shared_session = InMemoryAsyncSession()

    async def mock_db():
        yield shared_session

    app.dependency_overrides[get_current_user] = lambda: mock_user_org_a
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload
        invoice_text = (
            "TAX INVOICE\n"
            "Vendor: TechCorp Global\n"
            "Invoice Number: INV-2024-550\n"
            "Date: 2024-06-01\n"
            "Subtotal: $2,500.00\n"
            "Tax: $250.00\n"
            "Total: $2,750.00"
        )
        pdf_bytes = make_test_pdf(invoice_text)
        files = {"file": ("techcorp_invoice.pdf", pdf_bytes, "application/pdf")}
        upload_res = await client.post("/api/v1/documents/upload", files=files)

        assert upload_res.status_code == 201
        doc_id = upload_res.json()["data"]["id"]

        # 2. Analyze
        analyze_payload = {
            "document_id": doc_id,
            "task": "extract_information"
        }
        analyze_res = await client.post("/api/v1/agents/document/analyze", json=analyze_payload)

        assert analyze_res.status_code == 200
        result_json = analyze_res.json()
        assert result_json["success"] is True
        result_data = result_json["data"]

        assert result_data["document_id"] == doc_id
        assert result_data["document_type"] == "INVOICE"
        assert result_data["structured_data"]["vendor"] == "TechCorp Global"
        assert result_data["structured_data"]["total"] == "$2,750.00"
        assert result_data["confidence"] >= 0.90
        assert len(result_data["sources"]) > 0

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_supervisor_routes_to_document_agent(mock_user_org_a):
    """
    Integration Test: Verify that Supervisor Agent classifies document requests
    and routes them to document_agent.
    """
    shared_session = InMemoryAsyncSession()

    async def mock_db():
        yield shared_session

    app.dependency_overrides[get_current_user] = lambda: mock_user_org_a
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Prompt: "Summarize this PDF."
        payload = {"message": "Summarize this PDF."}
        res = await client.post("/api/v1/agents/supervisor/analyze", json=payload)

        assert res.status_code == 200
        decision = res.json()["data"]
        assert decision["task_type"] == "DOCUMENT_ANALYSIS"
        assert decision["selected_agent"] == "document_agent"
        assert decision["confidence"] >= 0.90

        # Prompt: "Read this invoice and extract the important information."
        payload_inv = {"message": "Read this invoice and extract the important information."}
        res_inv = await client.post("/api/v1/agents/supervisor/analyze", json=payload_inv)

        assert res_inv.status_code == 200
        decision_inv = res_inv.json()["data"]
        assert decision_inv["task_type"] == "DOCUMENT_ANALYSIS"
        assert decision_inv["selected_agent"] == "document_agent"

    app.dependency_overrides.clear()
