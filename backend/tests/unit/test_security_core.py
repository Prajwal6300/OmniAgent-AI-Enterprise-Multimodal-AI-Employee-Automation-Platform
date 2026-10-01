"""
OmniAgent AI — Core Security & Correctness Test Suite (Step 6 Verification)
Verifies:
1. Cryptographic prev_hash chaining and tamper detection on audit & action audit logs.
2. Fernet encryption-at-rest and secret redaction.
3. Redis distributed locking and token revocation list.
4. Dual-approver gating on CRITICAL risk actions and separation of duties.
5. sqlglot AST validation, limit enforcement, and system catalog blocking.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.database.security import SecurityValidator
from app.agents.database.sql_validator import SQLValidator
from app.core.encryption import decrypt_config, encrypt_config, redact_config
from app.core.redis import distributed_lock, is_token_revoked, revoke_token
from app.models.action import ActionAuditLog
from app.models.approval import Approval
from app.models.audit_log import AuditLog
from app.services.approval_service import ApprovalService
from app.services.audit_service import (
    record_action_audit_log,
    record_audit_log,
    verify_action_audit_log_chain,
    verify_audit_log_chain,
)

# ==============================================================================
# 1. Fernet Encryption & Redaction Tests
# ==============================================================================

def test_fernet_encryption_roundtrip():
    secret_data = {
        "api_key": "sk-test-1234567890abcdef",
        "webhook_url": "https://hooks.slack.com/services/T00/B00/X00",
        "nested": {"db_password": "super_secret_password_here"},
    }
    ciphertext = encrypt_config(secret_data)
    assert isinstance(ciphertext, str)
    assert "sk-test" not in ciphertext
    assert "super_secret" not in ciphertext

    decrypted = decrypt_config(ciphertext)
    assert decrypted == secret_data


def test_secret_redaction():
    secret_data = {
        "service_name": "slack_notifier",
        "api_token": "xoxb-1234567890-abcdef",
        "password": "mypassword123",
        "public_url": "https://example.com/api",
        "nested": {
            "secret_key": "topsecret",
            "port": 5432,
        },
    }
    redacted = redact_config(secret_data)
    assert redacted["service_name"] == "slack_notifier"
    assert redacted["public_url"] == "https://example.com/api"
    assert redacted["nested"]["port"] == 5432

    # Sensitive keys should be redacted or masked
    assert "xoxb-1234567890-abcdef" not in redacted["api_token"]
    assert "mypassword123" not in redacted["password"]
    assert "topsecret" not in redacted["nested"]["secret_key"]


# ==============================================================================
# 2. Redis Distributed Locking & Token Revocation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_distributed_lock_mutual_exclusion():
    lock_key = f"test_lock_{uuid4().hex}"
    async with distributed_lock(lock_key, timeout_seconds=2):
        # Nested attempt on same key should raise TimeoutError
        with pytest.raises(TimeoutError):
            async with distributed_lock(lock_key, timeout_seconds=1, retry_delay=0.01, max_retries=3):
                pass

    # After exiting first lock, it can be acquired again
    acquired_again = False
    async with distributed_lock(lock_key, timeout_seconds=1):
        acquired_again = True
    assert acquired_again is True


@pytest.mark.asyncio
async def test_token_revocation_lifecycle():
    token_jti = f"jti_{uuid4().hex}"
    assert await is_token_revoked(token_jti) is False

    await revoke_token(token_jti, expires_in_seconds=60)
    assert await is_token_revoked(token_jti) is True


# ==============================================================================
# 3. Cryptographic prev_hash Chaining Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_audit_log_hash_chaining_and_tamper_detection():
    org_id = uuid4()
    user_id = uuid4()

    # Simulate in-memory database storage
    stored_logs: list[AuditLog] = []

    mock_session = MagicMock(spec=AsyncSession)

    def mock_add(entry):
        stored_logs.append(entry)

    mock_session.add.side_effect = mock_add
    mock_session.flush = AsyncMock()

    async def mock_execute(stmt):
        mock_result = MagicMock()
        # Sort logs based on order_by
        asc = "ASC" in str(stmt)
        sorted_logs = sorted(stored_logs, key=lambda x: x.created_at, reverse=not asc)
        mock_result.scalar_one_or_none.return_value = sorted_logs[0] if sorted_logs else None
        mock_result.scalars.return_value.all.return_value = sorted_logs
        return mock_result

    mock_session.execute = mock_execute

    # Record 3 chained events
    entry1 = await record_audit_log(
        session=mock_session,
        organization_id=org_id,
        user_id=user_id,
        event_type="LOGIN",
        resource_type="auth",
        resource_id="user-1",
        details={"ip": "127.0.0.1"},
    )
    assert entry1.prev_hash == "0" * 64

    entry2 = await record_audit_log(
        session=mock_session,
        organization_id=org_id,
        user_id=user_id,
        event_type="DOCUMENT_UPLOAD",
        resource_type="document",
        resource_id="doc-123",
        details={"file": "contract.pdf"},
    )
    assert entry2.prev_hash == entry1.entry_hash

    entry3 = await record_audit_log(
        session=mock_session,
        organization_id=org_id,
        user_id=user_id,
        event_type="WORKFLOW_RUN",
        resource_type="workflow",
        resource_id="wf-999",
        details={"status": "STARTED"},
    )
    assert entry3.prev_hash == entry2.entry_hash

    # Verify intact chain
    is_valid, errors = await verify_audit_log_chain(mock_session, org_id)
    assert is_valid is True
    assert len(errors) == 0

    # Tamper with payload of entry 2
    entry2.details = {"file": "hacked_file.exe"}
    is_valid, errors = await verify_audit_log_chain(mock_session, org_id)
    assert is_valid is False
    assert any("Payload tampering detected" in e for e in errors)


@pytest.mark.asyncio
async def test_action_audit_log_hash_chaining():
    org_id = uuid4()
    user_id = uuid4()
    stored_actions: list[ActionAuditLog] = []

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.add.side_effect = lambda e: stored_actions.append(e)
    mock_session.flush = AsyncMock()

    async def mock_execute(stmt):
        mock_result = MagicMock()
        asc = "ASC" in str(stmt)
        sorted_actions = sorted(stored_actions, key=lambda x: x.created_at, reverse=not asc)
        mock_result.scalar_one_or_none.return_value = sorted_actions[0] if sorted_actions else None
        mock_result.scalars.return_value.all.return_value = sorted_actions
        return mock_result

    mock_session.execute = mock_execute

    act1 = await record_action_audit_log(
        session=mock_session,
        organization_id=org_id,
        user_id=user_id,
        action_id="act-1",
        action_type="DATABASE_READ",
        event_type="ACTION_COMPLETED",
        status="SUCCESS",
        risk_level="LOW",
        details={"rows": 10},
    )
    assert act1.prev_hash == "0" * 64

    act2 = await record_action_audit_log(
        session=mock_session,
        organization_id=org_id,
        user_id=user_id,
        action_id="act-2",
        action_type="EMAIL_SEND",
        event_type="ACTION_COMPLETED",
        status="SUCCESS",
        risk_level="HIGH",
        details={"recipient": "user@example.com"},
    )
    assert act2.prev_hash == act1.entry_hash

    is_valid, errors = await verify_action_audit_log_chain(mock_session, org_id)
    assert is_valid is True
    assert len(errors) == 0


# ==============================================================================
# 4. Dual-Approver & Separation of Duties Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_dual_approver_gating_critical_action():
    approval_id = uuid4()
    requester_id = uuid4()
    approver_one = uuid4()
    approver_two = uuid4()

    approval = Approval(
        id=approval_id,
        organization_id=uuid4(),
        action_type="STORAGE_DELETE",
        risk_level="CRITICAL",
        action_payload={"bucket": "prod-backups"},
        reason="Compliance retention cleanup",
        status="PENDING",
        requested_by=requester_id,
        created_at=datetime.now(UTC),
    )

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.get.return_value = approval
    mock_session.flush = AsyncMock()

    service = ApprovalService(mock_session)

    # 1. Requester cannot approve their own CRITICAL action (Separation of Duties)
    with pytest.raises(PermissionError, match="Separation of duties"):
        await service.decide(approval_id, requester_id, "APPROVED")

    # 2. First approver decides APPROVED -> moves to PENDING_SECOND_APPROVAL
    res1 = await service.decide(approval_id, approver_one, "APPROVED", reason="First signoff")
    assert res1.status == "PENDING_SECOND_APPROVAL"
    assert res1.decided_by == approver_one
    assert res1.second_decided_by is None

    # 3. Same approver attempting second signoff must be rejected
    with pytest.raises(ValueError, match="Dual-approver policy"):
        await service.decide(approval_id, approver_one, "APPROVED", reason="Duplicate signoff")

    # 4. Distinct second approver approves -> moves to APPROVED
    res2 = await service.decide(approval_id, approver_two, "APPROVED", reason="Second signoff verified")
    assert res2.status == "APPROVED"
    assert res2.decided_by == approver_one
    assert res2.second_decided_by == approver_two
    assert res2.signature_hmac is not None


@pytest.mark.asyncio
async def test_high_risk_action_requires_distinct_approver():
    approval_id = uuid4()
    requester_id = uuid4()
    independent_approver = uuid4()

    approval = Approval(
        id=approval_id,
        organization_id=uuid4(),
        action_type="EMAIL_SEND",
        risk_level="HIGH",
        action_payload={"to": "client@example.com"},
        reason="Quarterly statement",
        status="PENDING",
        requested_by=requester_id,
        created_at=datetime.now(UTC),
    )

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.get.return_value = approval
    mock_session.flush = AsyncMock()

    service = ApprovalService(mock_session)

    # Requester cannot approve
    with pytest.raises(PermissionError, match="Separation of duties"):
        await service.decide(approval_id, requester_id, "APPROVED")

    # Independent approver succeeds
    res = await service.decide(approval_id, independent_approver, "APPROVED")
    assert res.status == "APPROVED"
    assert res.decided_by == independent_approver


# ==============================================================================
# 5. sqlglot AST Validation & Limit Enforcement Tests
# ==============================================================================

def test_sqlglot_ast_blocks_destructive_ddl_and_dml():
    forbidden_queries = [
        "DROP TABLE customers",
        "TRUNCATE TABLE audit_logs",
        "DELETE FROM orders WHERE id = 1",
        "INSERT INTO users (email) VALUES ('hacked@evil.com')",
        "UPDATE accounts SET balance = 1000000",
        "ALTER TABLE users ADD COLUMN is_admin boolean",
    ]
    for q in forbidden_queries:
        is_safe, error = SecurityValidator.validate_read_only(q)
        assert is_safe is False
        assert error is not None


def test_sqlglot_ast_blocks_system_catalogs_and_functions():
    system_queries = [
        "SELECT * FROM pg_catalog.pg_tables",
        "SELECT * FROM information_schema.tables",
        "SELECT pg_read_file('/etc/passwd')",
        "SELECT pg_sleep(10)",
    ]
    for q in system_queries:
        is_safe, error = SecurityValidator.validate_read_only(q)
        assert is_safe is False
        assert error is not None


def test_sqlglot_limit_enforcement():
    # Injects limit when missing
    sql_no_limit = "SELECT id, name FROM customers"
    enforced = SecurityValidator.enforce_limit(sql_no_limit, max_limit=50)
    assert "LIMIT 50" in enforced.upper()

    # Caps limit when excessive
    sql_huge_limit = "SELECT id, name FROM customers LIMIT 10000"
    enforced = SecurityValidator.enforce_limit(sql_huge_limit, max_limit=100)
    assert "LIMIT 100" in enforced.upper()
    assert "10000" not in enforced


def test_sql_validator_ast_table_extraction():
    validator = SQLValidator()
    sql = "SELECT c.id, o.amount FROM customers c JOIN orders o ON c.id = o.customer_id WHERE c.organization_id = :organization_id"
    tables = validator.extract_tables(sql)
    assert "customers" in tables
    assert "orders" in tables
