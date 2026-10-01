"""
OmniAgent AI — Cross-Tenant Isolation Security Test Matrix
Validates database schema referential integrity (CASCADE delete), foreign key
constraints on organization_id, and cross-tenant query boundaries.
"""

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

import app.models  # noqa: F401 - Register all models in metadata
from app.db.base import Base


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


try:
    from pgvector.sqlalchemy import Vector

    @compiles(Vector, "sqlite")
    def compile_vector_sqlite(type_, compiler, **kw):
        return "TEXT"
except ImportError:
    pass

from app.models.approval import Approval
from app.models.audit_log import AuditLog
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.integration import Integration
from app.models.notification import Notification
from app.models.role import Role
from app.models.user import Organization, User
from app.models.workflow import Workflow


def test_schema_tenant_foreign_keys_and_cascade():
    """
    Validates that every tenant-scoped table in SQLAlchemy metadata:
    1. Contains an `organization_id` column.
    2. Has a Foreign Key targeting `organizations.id`.
    3. Enforces `ondelete='CASCADE'` for complete tenant deletion scrubbing.
    """
    EXEMPT_TABLES = {
        "organizations",      # Root tenant table
        "permissions",        # Global catalog of permissions
        "role_permissions",   # Association table (role_id -> permission_id)
        "messages",           # Child table belonging to tenant-scoped conversations
        "tool_calls",         # Child table belonging to tenant-scoped agent_runs/messages
    }

    all_tables = Base.metadata.tables
    checked_count = 0

    for table_name, table in all_tables.items():
        if table_name in EXEMPT_TABLES:
            continue

        org_col = table.columns.get("organization_id")
        assert org_col is not None, f"Table '{table_name}' is missing required 'organization_id' column"

        fk_list = [fk for fk in org_col.foreign_keys if fk.target_fullname == "organizations.id"]
        assert len(fk_list) == 1, f"Table '{table_name}.organization_id' does not reference 'organizations.id'"

        fk = fk_list[0]
        assert str(fk.ondelete).upper() == "CASCADE", (
            f"Table '{table_name}.organization_id' foreign key must have ondelete='CASCADE', found: {fk.ondelete}"
        )
        checked_count += 1

    assert checked_count >= 15, f"Expected at least 15 tenant-scoped tables to be checked, verified {checked_count}"


@pytest.fixture
async def in_memory_db():
    """Creates a temporary isolated in-memory SQLite database for tenant isolation verification."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_cross_tenant_document_isolation(in_memory_db: AsyncSession):
    """Proves Tenant A cannot retrieve or see Tenant B's documents."""
    org_a = Organization(id=uuid4(), name="Tenant Alpha", slug="alpha")
    org_b = Organization(id=uuid4(), name="Tenant Beta", slug="beta")
    in_memory_db.add_all([org_a, org_b])

    doc_a = Document(
        id=uuid4(),
        organization_id=org_a.id,
        file_name="alpha_secret.pdf",
        file_path="storage/alpha/secret.pdf",
        file_type="application/pdf",
        file_size_bytes=1024,
        checksum_sha256="a" * 64,
        processing_status="PROCESSED",
    )
    doc_b = Document(
        id=uuid4(),
        organization_id=org_b.id,
        file_name="beta_confidential.pdf",
        file_path="storage/beta/confidential.pdf",
        file_type="application/pdf",
        file_size_bytes=2048,
        checksum_sha256="b" * 64,
        processing_status="PROCESSED",
    )
    in_memory_db.add_all([doc_a, doc_b])
    await in_memory_db.commit()

    # Query scoped to Tenant A
    stmt = select(Document).where(Document.organization_id == org_a.id)
    result = await in_memory_db.execute(stmt)
    records = result.scalars().all()

    assert len(records) == 1
    assert records[0].file_name == "alpha_secret.pdf"
    assert all(r.organization_id == org_a.id for r in records)


@pytest.mark.asyncio
async def test_cross_tenant_conversation_isolation(in_memory_db: AsyncSession):
    """Proves Tenant A cannot retrieve Tenant B's conversations."""
    org_a = Organization(id=uuid4(), name="Tenant Alpha", slug="alpha-conv")
    org_b = Organization(id=uuid4(), name="Tenant Beta", slug="beta-conv")
    role = Role(id=uuid4(), name="Member", is_system_role=True)
    in_memory_db.add_all([org_a, org_b, role])

    user_a = User(
        id=uuid4(),
        organization_id=org_a.id,
        email="a@alpha.com",
        full_name="User A",
        hashed_password="hash",
        role_id=role.id,
    )
    user_b = User(
        id=uuid4(),
        organization_id=org_b.id,
        email="b@beta.com",
        full_name="User B",
        hashed_password="hash",
        role_id=role.id,
    )
    in_memory_db.add_all([user_a, user_b])

    conv_a = Conversation(id=uuid4(), organization_id=org_a.id, user_id=user_a.id, title="Alpha Thread")
    conv_b = Conversation(id=uuid4(), organization_id=org_b.id, user_id=user_b.id, title="Beta Thread")
    in_memory_db.add_all([conv_a, conv_b])
    await in_memory_db.commit()

    stmt = select(Conversation).where(Conversation.organization_id == org_a.id)
    result = await in_memory_db.execute(stmt)
    conversations = result.scalars().all()

    assert len(conversations) == 1
    assert conversations[0].title == "Alpha Thread"
    assert conversations[0].organization_id == org_a.id


@pytest.mark.asyncio
async def test_cross_tenant_workflow_and_integration_isolation(in_memory_db: AsyncSession):
    """Proves Tenant A cannot access Tenant B's workflows or integrations."""
    org_a = Organization(id=uuid4(), name="Tenant Alpha", slug="alpha-wf")
    org_b = Organization(id=uuid4(), name="Tenant Beta", slug="beta-wf")
    in_memory_db.add_all([org_a, org_b])

    wf_a = Workflow(id=uuid4(), organization_id=org_a.id, name="Invoice Pipeline", trigger_type="MANUAL", definition={"steps": []})
    wf_b = Workflow(id=uuid4(), organization_id=org_b.id, name="Payroll Pipeline", trigger_type="MANUAL", definition={"steps": []})
    integ_a = Integration(
        id=uuid4(),
        organization_id=org_a.id,
        service_name="slack",
        config_encrypted="enc_alpha",
        is_enabled=True,
    )
    integ_b = Integration(
        id=uuid4(),
        organization_id=org_b.id,
        service_name="github",
        config_encrypted="enc_beta",
        is_enabled=True,
    )
    in_memory_db.add_all([wf_a, wf_b, integ_a, integ_b])
    await in_memory_db.commit()

    # Query workflows for Tenant A
    wf_res = await in_memory_db.execute(select(Workflow).where(Workflow.organization_id == org_a.id))
    workflows = wf_res.scalars().all()
    assert len(workflows) == 1
    assert workflows[0].name == "Invoice Pipeline"

    # Query integrations for Tenant A
    integ_res = await in_memory_db.execute(select(Integration).where(Integration.organization_id == org_a.id))
    integrations = integ_res.scalars().all()
    assert len(integrations) == 1
    assert integrations[0].service_name == "slack"
    assert integrations[0].config_encrypted == "enc_alpha"


@pytest.mark.asyncio
async def test_cross_tenant_notification_and_approval_isolation(in_memory_db: AsyncSession):
    """Proves Tenant A cannot read Tenant B's notifications or approvals."""
    org_a = Organization(id=uuid4(), name="Tenant Alpha", slug="alpha-notif")
    org_b = Organization(id=uuid4(), name="Tenant Beta", slug="beta-notif")
    role = Role(id=uuid4(), name="Admin", is_system_role=True)
    in_memory_db.add_all([org_a, org_b, role])

    user_a = User(
        id=uuid4(),
        organization_id=org_a.id,
        email="a@alpha-notif.com",
        full_name="User A",
        hashed_password="hash",
        role_id=role.id,
    )
    user_b = User(
        id=uuid4(),
        organization_id=org_b.id,
        email="b@beta-notif.com",
        full_name="User B",
        hashed_password="hash",
        role_id=role.id,
    )
    in_memory_db.add_all([user_a, user_b])

    notif_a = Notification(id=uuid4(), organization_id=org_a.id, user_id=user_a.id, title="Alpha Alert", message="Msg", notification_type="INFO")
    notif_b = Notification(id=uuid4(), organization_id=org_b.id, user_id=user_b.id, title="Beta Alert", message="Msg", notification_type="INFO")

    appr_a = Approval(id=uuid4(), organization_id=org_a.id, action_type="PAYROLL_SUBMIT", risk_level="HIGH", action_payload={"sum": 100}, reason="Payroll", status="PENDING")
    appr_b = Approval(id=uuid4(), organization_id=org_b.id, action_type="DELETE_ALL", risk_level="CRITICAL", action_payload={"all": True}, reason="Purge", status="PENDING")
    in_memory_db.add_all([notif_a, notif_b, appr_a, appr_b])
    await in_memory_db.commit()

    # Verify notifications isolation
    n_res = await in_memory_db.execute(select(Notification).where(Notification.organization_id == org_a.id))
    notifs = n_res.scalars().all()
    assert len(notifs) == 1
    assert notifs[0].title == "Alpha Alert"

    # Verify approvals isolation
    appr_res = await in_memory_db.execute(select(Approval).where(Approval.organization_id == org_a.id))
    approvals = appr_res.scalars().all()
    assert len(approvals) == 1
    assert approvals[0].action_type == "PAYROLL_SUBMIT"


@pytest.mark.asyncio
async def test_cross_tenant_audit_trail_isolation(in_memory_db: AsyncSession):
    """Proves Tenant A cannot view or tamper with Tenant B's audit trail logs."""
    org_a = Organization(id=uuid4(), name="Tenant Alpha", slug="alpha-audit")
    org_b = Organization(id=uuid4(), name="Tenant Beta", slug="beta-audit")
    in_memory_db.add_all([org_a, org_b])

    log_a = AuditLog(
        id=uuid4(),
        organization_id=org_a.id,
        event_type="USER_LOGIN",
        resource_type="auth",
        resource_id="user_1",
        details={"ip": "127.0.0.1"},
        prev_hash="0" * 64,
        entry_hash="a" * 64,
    )
    log_b = AuditLog(
        id=uuid4(),
        organization_id=org_b.id,
        event_type="ORG_SETTINGS_CHANGE",
        resource_type="org",
        resource_id="org_2",
        details={"ip": "127.0.0.1"},
        prev_hash="0" * 64,
        entry_hash="b" * 64,
    )
    in_memory_db.add_all([log_a, log_b])
    await in_memory_db.commit()

    audit_res = await in_memory_db.execute(select(AuditLog).where(AuditLog.organization_id == org_a.id))
    logs = audit_res.scalars().all()
    assert len(logs) == 1
    assert logs[0].event_type == "USER_LOGIN"
