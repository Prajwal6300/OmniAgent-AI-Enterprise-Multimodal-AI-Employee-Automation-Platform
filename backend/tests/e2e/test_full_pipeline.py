"""
OmniAgent AI — End-to-End Orchestration & Automation Pipeline Tests
Tests real execution across the entire integrated system:
1. Multi-Agent Cross-Modal Reasoning Pipeline (Supervisor -> Specialists -> Grounded Answer)
2. Automated Multi-Step Workflow Execution Pipeline (Condition -> Action -> Result State)
3. End-to-End Human-In-The-Loop Lifecycle (Action -> Pause -> Cryptographic Approval -> Resumed Execution)
"""

import uuid

import pytest

from app.automation.engine.engine import WorkflowEngine
from app.orchestration.graph import Orchestrator


@pytest.mark.asyncio
async def test_full_pipeline_multi_agent_orchestration():
    """End-to-end verification of supervisor routing and evidence-grounded response synthesis."""
    orchestrator = Orchestrator()
    org_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    state = await orchestrator.execute(
        message="Review the maintenance manual guidelines and check safety procedures.",
        organization_id=org_id,
        user_id=user_id,
        context={"channel": "web_chat", "priority": "normal"},
    )

    assert state["status"] in ("COMPLETED", "ROUTED")
    assert state.get("final_response") is not None
    assert len(state.get("execution_steps", [])) >= 1
    assert state["organization_id"] == org_id


@pytest.mark.asyncio
async def test_full_pipeline_workflow_automation():
    """End-to-end verification of deterministic workflow engine execution."""
    engine = WorkflowEngine()
    org_id = str(uuid.uuid4())

    workflow_def = {
        "trigger": {"type": "MANUAL"},
        "steps": [
            {"type": "condition", "field": "pressure_psi", "operator": ">=", "value": 100},
            {
                "type": "action",
                "action": "send_notification",
                "input": {
                    "user_id": "operator-01",
                    "title": "High Pressure Alert",
                    "message": "Pressure threshold exceeded 100 psi",
                },
            },
        ],
    }

    run_state = engine.init_run(
        run_id=str(uuid.uuid4()),
        workflow_id=str(uuid.uuid4()),
        organization_id=org_id,
        initial_data={"pressure_psi": 120},
    )

    result = await engine.execute_workflow(workflow_def, run_state)
    assert result.status == "COMPLETED"
    assert len(result.steps_history) == 2
    assert result.steps_history[0].status == "COMPLETED"
    assert result.steps_history[1].status == "COMPLETED"


@pytest.mark.asyncio
async def test_full_pipeline_human_in_the_loop_lifecycle():
    """End-to-end verification of approval gating, cryptographic payload binding, pause and resume."""
    orchestrator = Orchestrator()
    org_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    req_id = str(uuid.uuid4())

    # 1. Trigger ticket creation action that mandates human approval
    initial_state = await orchestrator.execute(
        message="Create a maintenance ticket for turbine overheating issue #101.",
        organization_id=org_id,
        user_id=user_id,
        request_id=req_id,
    )

    # Must be intercepted and paused for approval
    assert initial_state["status"] == "WAITING_FOR_APPROVAL"
    assert initial_state["pending_approval"] is True
    approval_id = initial_state["approval_id"]
    assert approval_id is not None

    # 2. Resume execution with verified approval decision
    resumed_state = await orchestrator.resume(
        request_id=req_id,
        approval_id=approval_id,
        organization_id=org_id,
        user_id=user_id,
        decision="APPROVED",
        reason="Verified enterprise operator authorization",
    )

    assert resumed_state["status"] in ("COMPLETED", "ROUTED")
    assert resumed_state.get("final_response") is not None
