from agents.supervisor.schemas import SupervisorDecision
from agents.supervisor.prompts import SUPERVISOR_SYSTEM_PROMPT

class SupervisorAgent:
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name

    async def evaluate_step(self, state: dict) -> SupervisorDecision:
        # Evaluate state and determine next specialist or finish
        if not state.get("intermediate_steps"):
            return SupervisorDecision(next_agent="rag", reasoning="Initial grounding required")
        return SupervisorDecision(next_agent="end", reasoning="Task fulfilled", is_task_complete=True)
