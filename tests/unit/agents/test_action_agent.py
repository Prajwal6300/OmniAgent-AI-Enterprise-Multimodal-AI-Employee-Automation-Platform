"""
OmniAgent AI — Action Agent Comprehensive Unit Tests
Tests action registry, input validation, RBAC authorization, tenant isolation,
approval lifecycle & payload binding, idempotency, fake providers, verification,
and audit logging.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from uuid import UUID
import pytest

from agents.action.agent import ActionAgent
from agents.action.approval import (
    classify_action_risk,
    compute_payload_hash,
    create_approval_expiry,
    is_approval_expired,
    requires_approval,
    validate_approval_binding,
)
from agents.action.exceptions import (
    ActionError,
    ActionExecutionError,
    ActionExpiredError,
    ActionNotConfiguredError,
    ActionPermissionDeniedError,
    ActionSecurityError,
    ActionValidationError,
    ActionVerificationError,
)
from agents.action.executor import (
    ActionExecutor,
    FakeEmailProvider,
    FakeNotificationProvider,
    FakeReportProvider,
    FakeTicketProvider,
    SMTPEmailProvider,
)
from agents.action.idempotency import IdempotencyManager
from agents.action.registry import ActionRegistry, action_registry
from agents.action.schemas import (
    ActionContext,
    ActionRequest,
    ActionResult,
    ActionStatus,
    ActionType,
    CreateReportInput,
    CreateTicketInput,
    RiskLevel,
    SendEmailInput,
    SendNotificationInput,
)
from agents.action.security import ActionSecurityGuard
from agents.action.verifier import ActionVerifier


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def fake_executor():
    return ActionExecutor(
        email_provider=FakeEmailProvider(),
        notification_provider=FakeNotificationProvider(),
        ticket_provider=FakeTicketProvider(),
        report_provider=FakeReportProvider(),
    )


@pytest.fixture
def action_agent(fake_executor):
    return ActionAgent(executor=fake_executor)


@pytest.fixture
def admin_context():
    return ActionContext(
        user_id=str(uuid.uuid4()),
        organization_id="00000000-0000-0000-0000-000000000001",
        user_role="Admin",
        user_permissions=["actions.execute", "actions.approve"],
    )


@pytest.fixture
def operator_context():
    return ActionContext(
        user_id=str(uuid.uuid4()),
        organization_id="00000000-0000-0000-0000-000000000001",
        user_role="Operator",
        user_permissions=["actions.send_notification", "actions.create_report"],
    )


@pytest.fixture
def viewer_context():
    return ActionContext(
        user_id=str(uuid.uuid4()),
        organization_id="00000000-0000-0000-0000-000000000001",
        user_role="Viewer",
        user_permissions=[],
    )


# ==============================================================================
# 1. Action Registry Tests
# ==============================================================================

def test_registry_known_actions():
    """Verifies that all standard enterprise actions are properly registered."""
    assert action_registry.is_registered("send_email") is True
    assert action_registry.is_registered("SEND_EMAIL") is True  # Case insensitive
    assert action_registry.is_registered("send_notification") is True
    assert action_registry.is_registered("create_ticket") is True
    assert action_registry.is_registered("create_report") is True

    email_def = action_registry.get("send_email")
    assert email_def is not None
    assert email_def.risk_level == RiskLevel.MEDIUM
    assert email_def.approval_required is True


def test_registry_unknown_action_rejected():
    """Verifies that unknown or arbitrary actions are denied by default."""
    assert action_registry.is_registered("execute_arbitrary_code") is False
    assert action_registry.is_registered("drop_database") is False
    assert action_registry.get("unknown_tool_xyz") is None

    with pytest.raises(ActionValidationError) as excinfo:
        action_registry.validate_action("delete_everything")
    assert "unknown or not supported" in str(excinfo.value)


# ==============================================================================
# 2. Input Validation Tests
# ==============================================================================

def test_send_email_input_valid():
    inp = SendEmailInput(
        recipient="maintenance@example.com",
        subject="Report Ready",
        body="Inspection report is attached.",
    )
    assert inp.recipient == "maintenance@example.com"
    assert inp.subject == "Report Ready"


def test_send_email_input_invalid_email():
    with pytest.raises(Exception):
        SendEmailInput(
            recipient="not-an-email",
            subject="Hello",
            body="World",
        )


def test_send_email_header_injection_sanitization():
    inp = SendEmailInput(
        recipient="test@example.com",
        subject="Hello\r\nBcc: victim@example.com",
        body="Test body",
    )
    assert "\r" not in inp.subject
    assert "\n" not in inp.subject
    assert "Bcc: victim@example.com" in inp.subject


def test_create_ticket_priority_validation():
    inp = CreateTicketInput(
        title="Machine M-102 Overheating",
        description="Temperature sensor exceeds 95C",
        priority="HIGH",
    )
    assert inp.priority == "HIGH"

    with pytest.raises(Exception):
        CreateTicketInput(
            title="Invalid",
            description="Invalid priority test",
            priority="CRITICAL_UNSUPPORTED",  # not in Literal["LOW", "MEDIUM", "HIGH"]
        )


def test_oversized_payload_rejected():
    oversized_data = {"text": "A" * (300 * 1024)}  # 300 KB > 256 KB limit
    with pytest.raises(ActionValidationError) as exc:
        ActionSecurityGuard.validate_payload_size(oversized_data, max_kb=256)
    assert "exceeds allowable limit" in str(exc.value)


# ==============================================================================
# 3. RBAC Authorization Tests
# ==============================================================================

def test_admin_has_permission_for_all_actions():
    assert ActionSecurityGuard.check_permissions("send_email", "Admin", []) is True
    assert ActionSecurityGuard.check_permissions("create_ticket", "Admin", []) is True
    assert ActionSecurityGuard.check_permissions("create_report", "Admin", []) is True


def test_viewer_denied_ticket_and_email():
    assert ActionSecurityGuard.check_permissions("send_email", "Viewer", []) is False
    assert ActionSecurityGuard.check_permissions("create_ticket", "Viewer", []) is False


def test_explicit_permission_grant():
    assert ActionSecurityGuard.check_permissions(
        "create_ticket", "Viewer", ["actions.create_ticket"]
    ) is True


def test_approval_permission():
    assert ActionSecurityGuard.check_approval_permission("Admin", []) is True
    assert ActionSecurityGuard.check_approval_permission("Supervisor", []) is True
    assert ActionSecurityGuard.check_approval_permission("Operator", []) is False
    assert ActionSecurityGuard.check_approval_permission("Operator", ["actions.approve"]) is True


# ==============================================================================
# 4. Tenant Isolation Tests
# ==============================================================================

def test_tenant_isolation_enforcement():
    org_a = "00000000-0000-0000-0000-000000000001"
    org_b = "00000000-0000-0000-0000-000000000002"

    # Same org passes
    ActionSecurityGuard.validate_tenant_isolation(org_a, org_a)

    # Cross-tenant raises ActionSecurityError
    with pytest.raises(ActionSecurityError) as exc:
        ActionSecurityGuard.validate_tenant_isolation(org_a, org_b)
    assert "Tenant isolation violation" in str(exc.value)


# ==============================================================================
# 5. Approval Policy, Cryptographic Binding & Expiry Tests
# ==============================================================================

def test_approval_policy_determination():
    assert requires_approval("send_email") is True
    assert requires_approval("create_ticket") is True
    assert requires_approval("send_notification") is False
    assert requires_approval("create_report") is False


def test_payload_hash_binding_and_tampering_detection():
    org_id = "org_1"
    user_id = "user_1"
    action_type = "send_email"
    original_input = {
        "recipient": "maintenance@example.com",
        "subject": "Report",
        "body": "Safe body",
    }

    stored_hash = compute_payload_hash(org_id, user_id, action_type, original_input)
    assert isinstance(stored_hash, str)
    assert len(stored_hash) == 64

    # Identical input matches binding
    assert validate_approval_binding(stored_hash, org_id, user_id, action_type, original_input) is True

    # Tampered input (recipient changed) fails binding!
    tampered_input = {
        "recipient": "attacker@example.com",
        "subject": "Report",
        "body": "Safe body",
    }
    assert validate_approval_binding(stored_hash, org_id, user_id, action_type, tampered_input) is False


def test_approval_expiration():
    future_time = datetime.now(timezone.utc) + timedelta(minutes=15)
    assert is_approval_expired(future_time) is False

    past_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    assert is_approval_expired(past_time) is True


# ==============================================================================
# 6. Idempotency Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_idempotency_cache_and_deduplication():
    manager = IdempotencyManager()
    key = "idem_tx_999"
    org_id = "org_1"

    assert await manager.get(key, org_id) is None

    res = ActionResult(
        action_id="act_1",
        action_type="send_email",
        status="COMPLETED",
        success=True,
        message="Email sent",
        verified=True,
    )
    await manager.record_result(key, org_id, res)

    # Subsequent retrieval returns exact cached ActionResult
    cached = await manager.get(key, org_id)
    assert cached is not None
    assert cached.action_id == "act_1"
    assert cached.message == "Email sent"


# ==============================================================================
# 7. Action Execution with Deterministic Fake Providers
# ==============================================================================

@pytest.mark.asyncio
async def test_execute_notification_low_risk_auto_executes(action_agent, admin_context):
    """Low-risk notification does not require approval and executes immediately."""
    req = ActionRequest(
        action_type="send_notification",
        input={
            "user_id": str(uuid.uuid4()),
            "title": "System Update",
            "message": "Maintenance completed.",
            "channel": "IN_APP",
        },
    )
    result = await action_agent.execute(req, admin_context)

    assert result.success is True
    assert result.status == ActionStatus.COMPLETED.value
    assert result.verified is True
    assert result.requires_approval is False
    assert result.external_reference is not None


@pytest.mark.asyncio
async def test_execute_report_low_risk_auto_executes(action_agent, admin_context):
    """Low-risk report artifact creates report without approval."""
    req = ActionRequest(
        action_type="create_report",
        input={
            "report_type": "INSPECTION",
            "title": "Weekly Machine Inspection",
            "summary": "All machines operational.",
        },
    )
    result = await action_agent.execute(req, admin_context)

    assert result.success is True
    assert result.status == ActionStatus.COMPLETED.value
    assert result.verified is True
    assert result.requires_approval is False


@pytest.mark.asyncio
async def test_execute_email_requires_approval(action_agent, admin_context):
    """Medium-risk email pauses for approval when no approval_id is supplied."""
    req = ActionRequest(
        action_type="send_email",
        input={
            "recipient": "manager@example.com",
            "subject": "Inspection Alert",
            "body": "Issue detected on machine M-102.",
        },
    )
    result = await action_agent.execute(req, admin_context)

    assert result.requires_approval is True
    assert result.status == ActionStatus.PENDING_APPROVAL.value
    assert result.approval_id is not None
    assert result.success is False
    assert "Approval is required" in result.message


@pytest.mark.asyncio
async def test_execute_email_with_approval_token_succeeds(action_agent, admin_context):
    """Once approved, supplying the approval_id executes and verifies the email."""
    req = ActionRequest(
        action_type="send_email",
        input={
            "recipient": "manager@example.com",
            "subject": "Inspection Alert",
            "body": "Issue detected on machine M-102.",
        },
        approval_id="approved_token_123",
    )
    result = await action_agent.execute(req, admin_context)

    assert result.success is True
    assert result.status == ActionStatus.COMPLETED.value
    assert result.verified is True
    assert result.external_reference is not None
    assert "fake_msg_" in result.external_reference


@pytest.mark.asyncio
async def test_execute_ticket_with_approval_succeeds(action_agent, admin_context):
    """Creating a ticket executes and verifies ticket creation."""
    req = ActionRequest(
        action_type="create_ticket",
        input={
            "title": "Fix M-102 Motor",
            "description": "Excess vibration detected.",
            "priority": "HIGH",
            "machine_id": "M-102",
        },
        approval_id="approved_token_456",
    )
    result = await action_agent.execute(req, admin_context)

    assert result.success is True
    assert result.status == ActionStatus.COMPLETED.value
    assert result.verified is True
    assert result.external_reference is not None
    assert "fake_ticket_" in result.external_reference


# ==============================================================================
# 8. Post-Execution Verification Failure Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_verification_failure_detected():
    """If provider returns no external reference, verification fails and success is False."""
    broken_email_provider = FakeEmailProvider(missing_ref=True)
    broken_executor = ActionExecutor(email_provider=broken_email_provider)
    broken_agent = ActionAgent(executor=broken_executor)

    ctx = ActionContext(
        user_id=str(uuid.uuid4()),
        organization_id="00000000-0000-0000-0000-000000000001",
        user_role="Admin",
    )
    req = ActionRequest(
        action_type="send_email",
        input={
            "recipient": "manager@example.com",
            "subject": "Test",
            "body": "Body",
        },
        approval_id="approved_token_789",
    )
    result = await broken_agent.execute(req, ctx)

    assert result.verified is False
    assert result.success is False
    assert result.status == ActionStatus.VERIFICATION_FAILED.value


# ==============================================================================
# 9. Not Configured Provider Test
# ==============================================================================

@pytest.mark.asyncio
async def test_unconfigured_email_provider_returns_controlled_error():
    """Real SMTP provider with empty host returns unconfigured message without crashing."""
    real_unconfigured_executor = ActionExecutor(email_provider=SMTPEmailProvider())
    agent = ActionAgent(executor=real_unconfigured_executor)

    ctx = ActionContext(
        user_id=str(uuid.uuid4()),
        organization_id="00000000-0000-0000-0000-000000000001",
        user_role="Admin",
    )
    req = ActionRequest(
        action_type="send_email",
        input={
            "recipient": "test@example.com",
            "subject": "Test",
            "body": "Test body",
        },
        approval_id="approved_token_000",
    )
    result = await agent.execute(req, ctx)

    assert result.success is False
    assert "Email integration is not configured" in result.message


# ==============================================================================
# 10. Supervisor Direct Delegation Test
# ==============================================================================

@pytest.mark.asyncio
async def test_supervisor_run_action_agent_delegation():
    """Tests SupervisorAgent.run_action_agent() integration."""
    from agents.supervisor.agent import SupervisorAgent

    supervisor = SupervisorAgent()
    result = await supervisor.run_action_agent(
        action_type="send_notification",
        input_data={
            "user_id": str(uuid.uuid4()),
            "title": "Supervisor Notice",
            "message": "Notice dispatched from supervisor.",
            "channel": "IN_APP",
        },
        user_id=str(uuid.uuid4()),
        organization_id="00000000-0000-0000-0000-000000000001",
        user_role="Admin",
    )

    assert isinstance(result, ActionResult)
    assert result.success is True
    assert result.action_type == "send_notification"
