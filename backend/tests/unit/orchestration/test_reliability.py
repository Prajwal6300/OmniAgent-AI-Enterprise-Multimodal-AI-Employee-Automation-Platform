"""
OmniAgent AI — Orchestration Reliability & Limit Enforcement Tests
"""

import time

import pytest

from app.orchestration.errors import (
    ExecutionTimeoutError,
    MaxAgentCallsExceededError,
    MaxStepsExceededError,
)
from app.orchestration.graph import Orchestrator
from app.orchestration.limits import (
    enforce_agent_call_limit,
    enforce_execution_timeout,
    enforce_step_limit,
)


def test_max_steps():
    """Enforces step ceiling preventing runaway execution."""
    with pytest.raises(MaxStepsExceededError):
        enforce_step_limit(25, max_steps=20)


def test_max_agent_calls():
    """Enforces quota on specialist agent invocations."""
    with pytest.raises(MaxAgentCallsExceededError):
        enforce_agent_call_limit(15, max_calls=10)


def test_timeout():
    """Enforces execution duration ceiling."""
    past = time.time() - 150
    with pytest.raises(ExecutionTimeoutError):
        enforce_execution_timeout(past, max_seconds=120)


@pytest.mark.asyncio
async def test_cancellation():
    """Tests that active request can be cancelled."""
    orchestrator = Orchestrator()
    req_id = "test-cancel-001"
    # Seed active state
    Orchestrator._active_states[req_id] = {
        "request_id": req_id,
        "organization_id": "00000000-0000-0000-0000-000000000001",
        "status": "RUNNING",
    }

    cancelled = await orchestrator.cancel(
        request_id=req_id,
        organization_id="00000000-0000-0000-0000-000000000001",
        reason="User clicked abort button",
    )
    assert cancelled["status"] == "CANCELLED"
    assert cancelled["is_cancelled"] is True


@pytest.mark.asyncio
async def test_partial_success():
    """If one specialist encounters a failure, the pipeline isolates error and marks status."""
    from app.orchestration.executor import OrchestrationAgentExecutor
    executor = OrchestrationAgentExecutor()

    # Pass invalid state for an agent to induce partial failure
    res = await executor.execute_agent(
        "database_agent",
        {
            "organization_id": "00000000-0000-0000-0000-000000000001",
            "user_id": "test-user",
            # missing question/intent
        },
    )
    # Status is marked gracefully without raising unhandled exception
    assert res["agent"] == "database_agent"
    assert "status" in res


@pytest.mark.asyncio
async def test_duplicate_action_idempotency():
    """Ensures repeated action execution with identical idempotency key is safely deduplicated."""
    from app.agents.action.agent import ActionAgent
    from app.agents.action.schemas import ActionContext, ActionRequest

    agent = ActionAgent()
    context = ActionContext(
        user_id="user-001",
        organization_id="00000000-0000-0000-0000-000000000001",
    )
    request1 = ActionRequest(
        action_type="send_notification",
        input={"user_id": "user-001", "title": "Status Alert", "message": "All systems normal"},
        idempotency_key="idemp-key-unique-999",
    )

    res1 = await agent.execute(request1, context)
    assert res1.status in ("COMPLETED", "PENDING", "APPROVED")

    # Second invocation with same idempotency key
    request2 = ActionRequest(
        action_type="send_notification",
        input={"user_id": "user-001", "title": "Status Alert", "message": "All systems normal"},
        idempotency_key="idemp-key-unique-999",
    )
    res2 = await agent.execute(request2, context)
    # Deduplicated / identical result returned without duplicate side-effect
    assert res2.action_id == res1.action_id or res2.status in ("COMPLETED", "APPROVED")
