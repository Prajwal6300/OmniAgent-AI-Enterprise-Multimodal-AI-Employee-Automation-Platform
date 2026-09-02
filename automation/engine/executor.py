from automation.engine.state import WorkflowRunState

class StepExecutor:
    async def execute_step(self, step_name: str, step_type: str, context: dict) -> dict:
        return {"step": step_name, "status": "COMPLETED", "output": {}}
