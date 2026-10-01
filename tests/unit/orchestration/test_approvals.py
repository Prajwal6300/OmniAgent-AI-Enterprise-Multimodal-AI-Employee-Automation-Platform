"""
OmniAgent AI — Human-in-the-Loop Approval & Resume Tests
"""

from datetime import UTC, datetime, timedelta

import pytest
from app.orchestration.graph import Orchestrator

from agents.action.approval import (
    compute_payload_hash,
    is_approval_expired,
    requires_approval,
    validate_approval_binding,
)


def test_action_requires_approval():
    """Confirms high and medium risk actions require approval by policy."""
    assert requires_approval("create_ticket") is True
    assert requires_approval("send_email") is True
    assert requires_approval("send_notification") is False
    assert requires_approval("create_report") is False


@pytest.mark.asyncio
async def test_workflow_pauses_for_approval():
    """Tests that actions requiring approval pause workflow in WAITING_FOR_APPROVAL status."""
    orchestrator = Orchestrator()
    state = await orchestrator.execute(
        message="Create a maintenance ticket for the turbine overheating issue.",
        organization_id="00000000-0000-0000-0000-000000000001",
        user_id="00000000-0000-0000-0000-000000000001",
    )
    # The workflow must pause with an approval_id
    assert state["status"] == "WAITING_FOR_APPROVAL"
    assert state["pending_approval"] is True
    assert state.get("approval_id") is not None
    assert state.get("approval_detail") is not None
    assert state["approval_detail"]["action_type"] == "create_ticket"


@pytest.mark.asyncio
async def test_approved_workflow_resumes():
    """Tests that an approved action resumes execution and finalizes."""
    orchestrator = Orchestrator()
    req_id = "test-resume-req-001"
    state = await orchestrator.execute(
        message="Create a maintenance ticket for conveyor motor #4.",
        organization_id="00000000-0000-0000-0000-000000000001",
        user_id="00000000-0000-0000-0000-000000000001",
        request_id=req_id,
    )
    assert state["status"] == "WAITING_FOR_APPROVAL"
    appr_id = state["approval_id"]

    resumed_state = await orchestrator.resume(
        request_id=req_id,
        approval_id=appr_id,
        organization_id="00000000-0000-0000-0000-000000000001",
        user_id="00000000-0000-0000-0000-000000000001",
        decision="APPROVED",
    )
    assert resumed_state["status"] == "COMPLETED"
    assert resumed_state["pending_approval"] is False
    assert resumed_state.get("action_result") is not None


@pytest.mark.asyncio
async def test_rejected_action_does_not_execute():
    """Tests that a rejected action cancels the execution flow and does not perform side effects."""
    orchestrator = Orchestrator()
    req_id = "test-reject-req-002"
    state = await orchestrator.execute(
        message="Create a maintenance ticket for cooling unit.",
        organization_id="00000000-0000-0000-0000-000000000001",
        user_id="00000000-0000-0000-0000-000000000001",
        request_id=req_id,
    )
    appr_id = state["approval_id"]

    resumed_state = await orchestrator.resume(
        request_id=req_id,
        approval_id=appr_id,
        organization_id="00000000-0000-0000-0000-000000000001",
        user_id="00000000-0000-0000-0000-000000000001",
        decision="REJECTED",
        reason="Not justified by telemetry.",
    )
    assert resumed_state["status"] == "CANCELLED"
    assert "rejected" in resumed_state["final_response"].lower()


def test_expired_approval():
    """Tests that an expired approval timestamp is correctly detected."""
    expired_time = datetime.now(UTC) - timedelta(minutes=35)
    valid_time = datetime.now(UTC) + timedelta(minutes=10)

    assert is_approval_expired(expired_time) is True
    assert is_approval_expired(valid_time) is False


def test_modified_payload_invalidates_approval():
    """Tests that modifying action parameters after approval invalidates cryptographic binding."""
    org_id = "org-123"
    user_id = "user-456"
    action_type = "create_ticket"
    original_input = {"title": "Repair valve 4", "priority": "HIGH"}

    payload_hash = compute_payload_hash(
        organization_id=org_id,
        user_id=user_id,
        action_type=action_type,
        normalized_input=original_input,
    )

    # Legitimate payload matches
    assert validate_approval_binding(
        stored_payload_hash=payload_hash,
        organization_id=org_id,
        user_id=user_id,
        action_type=action_type,
        normalized_input=original_input,
    ) is True

    # Tampered payload fails
    tampered_input = {"title": "Repair valve 4", "priority": "LOW"}
    assert validate_approval_binding(
        stored_payload_hash=payload_hash,
        organization_id=org_id,
        user_id=user_id,
        action_type=action_type,
        normalized_input=tampered_input,
    ) is False
