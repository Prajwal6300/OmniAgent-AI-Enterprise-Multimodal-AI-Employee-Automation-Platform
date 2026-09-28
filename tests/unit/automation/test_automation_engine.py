"""
OmniAgent AI — Automation Engine Unit Tests
Tests WorkflowEngine execution, condition evaluation, approval pauses, and step lifecycle.
"""

import pytest
from automation.conditions.evaluator import ConditionEvaluator
from automation.conditions.rules import Rule
from automation.engine.engine import WorkflowEngine
from automation.triggers.base import EventTrigger, ManualTrigger, ScheduleTrigger


def test_condition_evaluator_all_operators():
    evaluator = ConditionEvaluator()

    ctx = {
        "confidence": 0.95,
        "status": "FAILED",
        "error_count": 5,
        "nested": {"machine": {"health": 0.4}},
    }

    # equals / not_equals
    assert evaluator.evaluate(Rule(field="status", operator="equals", value="FAILED"), ctx) is True
    assert evaluator.evaluate(Rule(field="status", operator="not_equals", value="OK"), ctx) is True

    # numeric comparisons
    assert evaluator.evaluate(Rule(field="confidence", operator="greater_than", value=0.9), ctx) is True
    assert evaluator.evaluate(Rule(field="error_count", operator="less_than_or_equal", value=5), ctx) is True

    # nested dot notation
    assert evaluator.evaluate(Rule(field="nested.machine.health", operator="<", value=0.5), ctx) is True

    # contains
    assert evaluator.evaluate(Rule(field="status", operator="contains", value="FAIL"), ctx) is True

    # exists
    assert evaluator.evaluate(Rule(field="confidence", operator="exists"), ctx) is True
    assert evaluator.evaluate(Rule(field="missing_field", operator="not_exists"), ctx) is True


@pytest.mark.asyncio
async def test_trigger_evaluation():
    manual = ManualTrigger()
    assert await manual.evaluate({}, {}) is True

    event = EventTrigger("defect_detected")
    assert await event.evaluate({"event": "defect_detected"}, {}) is True
    assert await event.evaluate({"event": "shift_started"}, {}) is False


@pytest.mark.asyncio
async def test_workflow_engine_execution():
    engine = WorkflowEngine()
    workflow_def = {
        "trigger": {"type": "MANUAL"},
        "steps": [
            {"type": "condition", "field": "count", "operator": ">", "value": 0},
            {"type": "action", "action": "send_notification", "input": {"title": "Batch notice"}},
        ],
    }

    run_state = engine.init_run(
        run_id="run-test-001",
        workflow_id="wf-test-001",
        organization_id="00000000-0000-0000-0000-000000000001",
        initial_data={"count": 10},
    )

    result = await engine.execute_workflow(workflow_def, run_state)
    assert result.status == "COMPLETED"
    assert len(result.steps_history) == 2


@pytest.mark.asyncio
async def test_workflow_engine_approval_pause_and_resume():
    engine = WorkflowEngine()
    workflow_def = {
        "trigger": {"type": "MANUAL"},
        "steps": [
            {"type": "condition", "field": "risk", "operator": "==", "value": "HIGH"},
            {"type": "approval", "required": True},
            {"type": "action", "action": "create_ticket", "input": {"title": "Urgent machine fix", "description": "Hydraulic failure detected"}},
        ],
    }

    run_state = engine.init_run(
        run_id="run-pause-002",
        workflow_id="wf-pause-002",
        organization_id="00000000-0000-0000-0000-000000000001",
        initial_data={"risk": "HIGH"},
    )

    # 1. Execute until approval gate -> status becomes PAUSED
    result = await engine.execute_workflow(workflow_def, run_state)
    assert result.status == "PAUSED"
    assert result.current_step == 2

    # 2. Resume with approval token
    resumed = await engine.resume_run(
        run_id="run-pause-002",
        workflow_def=workflow_def,
        approval_id="appr-12345",
        decision="APPROVED",
    )
    assert resumed.status == "COMPLETED"
