import pytest
from agents.supervisor.agent import SupervisorAgent

@pytest.mark.asyncio
async def test_supervisor_initial_routing():
    agent = SupervisorAgent()
    state = {"intermediate_steps": [], "task_goal": "Analyze financial invoice"}
    decision = await agent.evaluate_step(state)
    assert decision.next_agent in ["rag", "document", "end"]
