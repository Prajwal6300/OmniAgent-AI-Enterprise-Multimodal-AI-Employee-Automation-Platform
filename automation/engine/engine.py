"""
OmniAgent AI — Automation Workflow Engine
Orchestrates sequential and conditional execution of multi-step enterprise workflows.
Handles pausing on approvals, execution limits, cancellation, and persistence.
"""

from datetime import UTC, datetime
import time
from typing import Any
import uuid

from automation.engine.executor import StepExecutor
from automation.engine.state import WorkflowRunState
from automation.limits import WORKFLOW_MAX_EXECUTION_SECONDS, WORKFLOW_MAX_STEPS
from automation.validator import validate_workflow_definition


class WorkflowEngine:
    """Core automation execution runtime."""

    def __init__(self, session: Any = None):
        self.session = session
        self.executor = StepExecutor(session=session)
        self._active_runs: dict[str, WorkflowRunState] = {}

    def init_run(
        self,
        run_id: str,
        workflow_id: str,
        organization_id: str | dict[str, Any] = "default_org",
        initial_data: dict[str, Any] | None = None,
    ) -> WorkflowRunState:
        if isinstance(organization_id, dict):
            initial_data = organization_id
            org_id = "default_org"
        else:
            org_id = organization_id or "default_org"

        state = WorkflowRunState(
            run_id=run_id,
            workflow_id=workflow_id,
            organization_id=org_id,
            status="PENDING",
            context=initial_data or {},
        )
        self._active_runs[run_id] = state
        return state

    async def execute_workflow(
        self,
        workflow_def: dict[str, Any],
        run_state: WorkflowRunState,
    ) -> WorkflowRunState:
        """Executes a validated workflow definition until completion, failure, or approval pause."""
        validated = validate_workflow_definition(workflow_def)
        steps = validated.get("steps", [])
        run_state.total_steps = len(steps)
        run_state.status = "RUNNING"
        self._active_runs[run_state.run_id] = run_state

        start_time = time.time()

        start_idx = run_state.current_step
        for idx in range(start_idx, len(steps)):
            # Check limits
            if idx >= WORKFLOW_MAX_STEPS:
                run_state.status = "FAILED"
                run_state.error = f"Workflow exceeded max step limit ({WORKFLOW_MAX_STEPS})."
                run_state.completed_at = datetime.now(UTC)
                return run_state

            if time.time() - start_time > WORKFLOW_MAX_EXECUTION_SECONDS:
                run_state.status = "FAILED"
                run_state.error = f"Workflow exceeded timeout limit ({WORKFLOW_MAX_EXECUTION_SECONDS}s)."
                run_state.completed_at = datetime.now(UTC)
                return run_state

            step = steps[idx]
            run_state.current_step = idx + 1

            result = await self.executor.execute_step(step, idx + 1, run_state)
            run_state.steps_history.append(result)

            if result.status == "PAUSED":
                run_state.status = "PAUSED"
                # Execution paused at this step for human approval
                return run_state

            if result.status == "FAILED":
                run_state.status = "FAILED"
                run_state.error = result.error or f"Step {idx + 1} ({result.name}) failed."
                run_state.completed_at = datetime.now(UTC)
                return run_state

            # If condition skipped, we continue or branch
            if result.status == "SKIPPED":
                continue

        run_state.status = "COMPLETED"
        run_state.completed_at = datetime.now(UTC)
        return run_state

    async def resume_run(
        self,
        run_id: str,
        workflow_def: dict[str, Any],
        approval_id: str,
        decision: str = "APPROVED",
        reason: str | None = None,
    ) -> WorkflowRunState:
        """Resumes a paused workflow run following human approval decision."""
        run_state = self._active_runs.get(run_id)
        if not run_state:
            raise ValueError(f"Workflow run '{run_id}' not found.")

        if run_state.status != "PAUSED":
            raise ValueError(f"Workflow run is in '{run_state.status}', not PAUSED.")

        if decision.upper() == "REJECTED":
            run_state.status = "CANCELLED"
            run_state.error = f"Workflow rejected by reviewer: {reason or 'Denied'}"
            run_state.completed_at = datetime.now(UTC)
            return run_state

        run_state.context["approval_granted"] = True
        run_state.context["approval_id"] = approval_id
        return await self.execute_workflow(workflow_def, run_state)

    def cancel_run(self, run_id: str, reason: str = "User cancelled run") -> WorkflowRunState:
        run_state = self._active_runs.get(run_id)
        if not run_state:
            raise ValueError(f"Workflow run '{run_id}' not found.")

        run_state.status = "CANCELLED"
        run_state.error = reason
        run_state.completed_at = datetime.now(UTC)
        return run_state
