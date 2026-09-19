"""
OmniAgent AI — Action Agent Integration & API Tests
Verifies FastAPI endpoints:
- POST /api/v1/agents/action/execute
- GET  /api/v1/agents/action/approvals
- POST /api/v1/agents/action/approvals/{approval_id}/approve
- POST /api/v1/agents/action/approvals/{approval_id}/reject
- GET  /api/v1/agents/action/history
Along with authentication, tenant isolation, RBAC permissions, and approval flows.
"""

from datetime import datetime, timezone
from typing import Any
import uuid
from uuid import UUID
import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.main import app
from app.models.action import ActionApproval, ActionRecord
from app.models.role import Permission, Role
from app.models.user import User


class DummyActionSession:
    """Mock async session simulating database transactions for Action Agent."""

    def __init__(self):
        self.approvals: dict[UUID, ActionApproval] = {}
        self.actions: dict[UUID, ActionRecord] = {}

    def add(self, obj: Any):
        if isinstance(obj, ActionApproval):
            self.approvals[obj.id] = obj
        elif isinstance(obj, ActionRecord):
            self.actions[obj.id] = obj

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def close(self):
        pass

    async def get(self, model_cls: Any, ident: Any):
        uuid_ident = UUID(str(ident))
        if model_cls == ActionApproval:
            return self.approvals.get(uuid_ident)
        elif model_cls == ActionRecord:
            return self.actions.get(uuid_ident)
        return None

    async def execute(self, stmt: Any, params: Any = None):
        class DummyResult:
            def __init__(self, data: list):
                self._data = data

            def scalars(self):
                class DummyScalars:
                    def __init__(self, data: list):
                        self._data = data

                    def all(self):
                        return self._data
                return DummyScalars(self._data)

        # Handle list_approvals or get_history query
        stmt_str = str(stmt)
        if "action_approvals" in stmt_str:
            return DummyResult(list(self.approvals.values()))
        elif "actions" in stmt_str:
            return DummyResult(list(self.actions.values()))
        return DummyResult([])


@pytest.fixture
def org_id_a():
    return uuid.uuid4()


@pytest.fixture
def org_id_b():
    return uuid.uuid4()


@pytest.fixture
def admin_user(org_id_a):
    admin_role = Role(
        id=uuid.uuid4(),
        name="Admin",
        is_system_role=True,
        permissions=[
            Permission(id=uuid.uuid4(), name="actions.execute", category="actions"),
            Permission(id=uuid.uuid4(), name="actions.approve", category="actions"),
        ],
    )
    return User(
        id=uuid.uuid4(),
        organization_id=org_id_a,
        email="admin@enterprise.omniagent.ai",
        full_name="Enterprise Admin",
        is_active=True,
        is_verified=True,
        role_id=admin_role.id,
        role=admin_role,
    )


@pytest.fixture
def viewer_user(org_id_a):
    viewer_role = Role(
        id=uuid.uuid4(),
        name="Viewer",
        is_system_role=True,
        permissions=[],
    )
    return User(
        id=uuid.uuid4(),
        organization_id=org_id_a,
        email="viewer@enterprise.omniagent.ai",
        full_name="Read-Only Viewer",
        is_active=True,
        is_verified=True,
        role_id=viewer_role.id,
        role=viewer_role,
    )


# ==============================================================================
# 1. Unauthenticated Endpoint Protection
# ==============================================================================

@pytest.mark.asyncio
async def test_action_execute_unauthenticated():
    """Endpoints reject unauthenticated calls with 401 Unauthorized."""
    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/agents/action/execute",
            json={"action_type": "send_notification", "input": {"user_id": "u1", "title": "t", "message": "m"}},
        )
        assert res.status_code == 401


# ==============================================================================
# 2. Action Execution & Approval Flow
# ==============================================================================

@pytest.mark.asyncio
async def test_action_execute_low_risk_notification(admin_user):
    """Low-risk action executes immediately returning 200 and success=True."""
    dummy_session = DummyActionSession()

    async def mock_db():
        yield dummy_session

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "action_type": "send_notification",
            "input": {
                "user_id": str(admin_user.id),
                "title": "Machine Alert",
                "message": "Maintenance completed on M-102.",
                "channel": "IN_APP",
            },
        }
        res = await client.post("/api/v1/agents/action/execute", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        data = body["data"]
        assert data["success"] is True
        assert data["status"] == "COMPLETED"
        assert data["requires_approval"] is False

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_action_execute_medium_risk_email_pauses_for_approval(admin_user):
    """Medium-risk action pauses for human approval returning requires_approval=True."""
    dummy_session = DummyActionSession()

    async def mock_db():
        yield dummy_session

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "action_type": "send_email",
            "input": {
                "recipient": "maintenance@example.com",
                "subject": "Inspection Report",
                "body": "Report ready for review.",
            },
        }
        res = await client.post("/api/v1/agents/action/execute", json=payload)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["requires_approval"] is True
        assert data["status"] == "PENDING_APPROVAL"
        assert data["approval_id"] is not None
        assert data["success"] is False

    app.dependency_overrides.clear()


# ==============================================================================
# 3. Approval List, Approve & Reject Endpoints
# ==============================================================================

@pytest.mark.asyncio
async def test_action_approvals_list_and_approve(admin_user):
    """Admin can list pending approvals and approve an action."""
    dummy_session = DummyActionSession()

    # Pre-populate an approval record
    action_id = uuid.uuid4()
    approval_id = uuid.uuid4()
    sample_input = {"recipient": "manager@example.com", "subject": "Test", "body": "Body"}
    from agents.action.approval import compute_payload_hash, create_approval_expiry

    p_hash = compute_payload_hash(
        str(admin_user.organization_id),
        str(admin_user.id),
        "send_email",
        sample_input,
    )

    action_rec = ActionRecord(
        id=action_id,
        organization_id=admin_user.organization_id,
        requested_by=admin_user.id,
        action_type="send_email",
        risk_level="MEDIUM",
        status="PENDING_APPROVAL",
        input_hash=p_hash,
        input_payload=sample_input,
        created_at=datetime.now(timezone.utc),
    )
    approval_rec = ActionApproval(
        id=approval_id,
        organization_id=admin_user.organization_id,
        action_id=action_id,
        requested_by=admin_user.id,
        action_type="send_email",
        payload_summary="Send email to manager@example.com",
        risk_level="MEDIUM",
        status="PENDING",
        payload_hash=p_hash,
        expires_at=create_approval_expiry(30),
        created_at=datetime.now(timezone.utc),
    )
    dummy_session.add(action_rec)
    dummy_session.add(approval_rec)

    async def mock_db():
        yield dummy_session

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. List approvals
        res_list = await client.get("/api/v1/agents/action/approvals")
        assert res_list.status_code == 200
        items = res_list.json()["data"]
        assert len(items) >= 1
        assert items[0]["action_type"] == "send_email"

        # 2. Approve action
        res_appr = await client.post(
            f"/api/v1/agents/action/approvals/{approval_id}/approve",
            json={"reason": "Approved by maintenance lead"},
        )
        assert res_appr.status_code == 200
        appr_data = res_appr.json()["data"]
        assert appr_data["status"] == "APPROVED"
        assert appr_data["approved_by"] == str(admin_user.id)

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_action_approval_rejected_by_viewer_forbidden(viewer_user):
    """User without approval permissions (Viewer) is forbidden from approving/rejecting."""
    dummy_session = DummyActionSession()

    async def mock_db():
        yield dummy_session

    app.dependency_overrides[get_current_user] = lambda: viewer_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/agents/action/approvals/{uuid.uuid4()}/approve",
            json={"reason": "Unauthorized attempt"},
        )
        assert res.status_code == 403

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_action_approval_cross_tenant_isolation(admin_user, org_id_b):
    """Admin of Org A cannot approve an action belonging to Org B."""
    dummy_session = DummyActionSession()

    # Pre-populate approval belonging to Org B
    approval_id = uuid.uuid4()
    from agents.action.approval import create_approval_expiry
    foreign_approval = ActionApproval(
        id=approval_id,
        organization_id=org_id_b,  # Different org!
        action_id=uuid.uuid4(),
        requested_by=uuid.uuid4(),
        action_type="send_email",
        payload_summary="Send email",
        risk_level="MEDIUM",
        status="PENDING",
        payload_hash="dummy_hash",
        expires_at=create_approval_expiry(30),
    )
    dummy_session.add(foreign_approval)

    async def mock_db():
        yield dummy_session

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/agents/action/approvals/{approval_id}/approve",
            json={"reason": "Attempting cross tenant approval"},
        )
        assert res.status_code == 403
        assert "another organization" in res.json()["detail"].lower()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_action_history_endpoint(admin_user):
    """Verifies that GET /api/v1/agents/action/history returns 200 and history list."""
    dummy_session = DummyActionSession()

    async def mock_db():
        yield dummy_session

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_db_session] = mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/agents/action/history")
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert isinstance(res.json()["data"], list)

    app.dependency_overrides.clear()
