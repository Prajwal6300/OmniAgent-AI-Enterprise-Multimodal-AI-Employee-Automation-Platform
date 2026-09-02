from typing import Dict, Any
from automation.engine.state import WorkflowRunState

class WorkflowEngine:
    def __init__(self):
        self._active_runs: Dict[str, WorkflowRunState] = {}

    def init_run(self, run_id: str, workflow_id: str, initial_data: dict) -> WorkflowRunState:
        state = WorkflowRunState(
            run_id=run_id,
            workflow_id=workflow_id,
            status="PENDING",
            context=initial_data
        )
        self._active_runs[run_id] = state
        return state
