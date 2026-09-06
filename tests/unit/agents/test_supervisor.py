import pytest

from agents.supervisor.agent import SupervisorAgent
from agents.supervisor.providers import MockLLMProvider
from agents.supervisor.schemas import AgentTarget, TaskType


@pytest.fixture
def supervisor():
    return SupervisorAgent()


@pytest.mark.asyncio
async def test_supervisor_initial_routing(supervisor):
    """Legacy backward compatibility test for multi-agent graph."""
    state = {"intermediate_steps": [], "task_goal": "Analyze financial invoice"}
    decision = await supervisor.evaluate_step(state)
    assert decision.next_agent in ["rag", "document", "end"]


@pytest.mark.asyncio
async def test_1_summarize_pdf(supervisor):
    """Test 1: PDF analysis routed to document_agent."""
    decision = await supervisor.analyze("Summarize this PDF")
    assert decision.task_type == TaskType.DOCUMENT_ANALYSIS.value
    assert decision.selected_agent == AgentTarget.DOCUMENT_AGENT.value
    assert decision.confidence >= 0.90
    assert decision.requires_approval is False
    assert len(decision.task_plan) > 0


@pytest.mark.asyncio
async def test_2_database_query(supervisor):
    """Test 2: SQL / Database query routed to database_agent."""
    decision = await supervisor.analyze("What is the total sales amount from the database?")
    assert decision.task_type == TaskType.DATABASE_QUERY.value
    assert decision.selected_agent == AgentTarget.DATABASE_AGENT.value
    assert decision.confidence >= 0.90
    assert decision.requires_approval is False
    assert len(decision.task_plan) > 0


@pytest.mark.asyncio
async def test_3_knowledge_search(supervisor):
    """Test 3: Policy knowledge retrieval routed to rag_agent."""
    decision = await supervisor.analyze("Find information about our leave policy")
    assert decision.task_type == TaskType.KNOWLEDGE_SEARCH.value
    assert decision.selected_agent == AgentTarget.RAG_AGENT.value
    assert decision.confidence >= 0.90
    assert decision.requires_approval is False
    assert len(decision.task_plan) > 0


@pytest.mark.asyncio
async def test_4_image_analysis(supervisor):
    """Test 4: Machine / photo visual inspection routed to vision_agent."""
    decision = await supervisor.analyze("Analyze this machine image")
    assert decision.task_type == TaskType.IMAGE_ANALYSIS.value
    assert decision.selected_agent == AgentTarget.VISION_AGENT.value
    assert decision.confidence >= 0.90
    assert decision.requires_approval is False
    assert len(decision.task_plan) > 0


@pytest.mark.asyncio
async def test_5_send_report_action(supervisor):
    """Test 5: Report dispatch routed to action_agent with requires_tool = True."""
    decision = await supervisor.analyze("Send this report to the manager")
    assert decision.selected_agent == AgentTarget.ACTION_AGENT.value
    assert decision.requires_tool is True
    assert decision.confidence >= 0.90
    assert len(decision.task_plan) > 0


@pytest.mark.asyncio
async def test_6_delete_employee_record(supervisor):
    """Test 6: Destructive action marked high risk with requires_approval = True."""
    decision = await supervisor.analyze("Delete the employee record")
    assert decision.priority == "high"
    assert decision.requires_approval is True
    assert decision.requires_tool is True
    assert len(decision.task_plan) > 0


@pytest.mark.asyncio
async def test_7_empty_message(supervisor):
    """Test 7: Empty message returns validation error fallback."""
    decision = await supervisor.analyze("")
    assert decision.task_type == TaskType.UNKNOWN.value
    assert decision.selected_agent == AgentTarget.SUPERVISOR.value
    assert decision.confidence == 0.0
    assert "cannot be empty" in decision.explanation or "Validation" in decision.explanation


@pytest.mark.asyncio
async def test_7_whitespace_only_message(supervisor):
    """Test 7b: Whitespace only message returns validation error fallback."""
    decision = await supervisor.analyze("     ")
    assert decision.task_type == TaskType.UNKNOWN.value
    assert decision.confidence == 0.0


@pytest.mark.asyncio
async def test_8_unknown_request(supervisor):
    """Test 8: Ambiguous or unknown request returns UNKNOWN classification."""
    decision = await supervisor.analyze("asdfghjk qwertyuiop")
    assert decision.task_type == TaskType.UNKNOWN.value
    assert decision.selected_agent == AgentTarget.SUPERVISOR.value
    assert decision.confidence == 0.0


@pytest.mark.asyncio
async def test_mock_llm_provider_custom_response():
    """Unit test using MockLLMProvider with custom payload."""
    custom_payload = {
        "intent": "custom_financial_audit",
        "task_type": "DATA_ANALYSIS",
        "capability": "data_analysis",
        "selected_agent": "reasoning_agent",
        "priority": "high",
        "confidence": 0.98,
        "requires_tool": True,
        "requires_approval": True,
        "task_plan": ["Audit ledgers", "Calculate delta"],
        "explanation": "Custom test reasoning."
    }
    mock_provider = MockLLMProvider(custom_response=custom_payload)
    agent = SupervisorAgent(provider=mock_provider)
    
    decision = await agent.analyze("Perform ledger reconciliation")
    assert decision.intent == "custom_financial_audit"
    assert decision.task_type == "DATA_ANALYSIS"
    assert decision.selected_agent == "reasoning_agent"
    assert decision.confidence == 0.98
    assert decision.requires_approval is True


@pytest.mark.asyncio
async def test_mock_llm_provider_timeout_fallback():
    """Verify SupervisorAgent does not crash on LLM timeout, returns safe fallback."""
    timeout_provider = MockLLMProvider(simulate_timeout=True)
    agent = SupervisorAgent(provider=timeout_provider)
    
    decision = await agent.analyze("Check these unclassified records")
    assert decision.task_type == TaskType.UNKNOWN.value
    assert decision.selected_agent == AgentTarget.SUPERVISOR.value
    assert decision.confidence == 0.0
    assert decision.requires_approval is False


@pytest.mark.asyncio
async def test_mock_llm_provider_malformed_json_fallback():
    """Verify SupervisorAgent gracefully handles malformed provider output."""
    corrupt_provider = MockLLMProvider(simulate_malformed=True)
    agent = SupervisorAgent(provider=corrupt_provider)
    
    decision = await agent.analyze("Process unstructured input")
    assert decision.task_type == TaskType.UNKNOWN.value
    assert decision.confidence == 0.0


@pytest.mark.asyncio
async def test_task_plan_does_not_expose_hidden_cot(supervisor):
    """Verify that operational task plans contain clean action steps and no internal CoT."""
    decision = await supervisor.analyze("Analyze invoice INV-1002 and extract line items")
    for step in decision.task_plan:
        assert not step.lower().startswith("let's think")
        assert not step.lower().startswith("thinking:")
        assert not step.lower().startswith("<thought>")
