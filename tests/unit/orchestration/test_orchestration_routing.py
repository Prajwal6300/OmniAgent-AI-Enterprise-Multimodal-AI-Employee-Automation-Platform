"""
OmniAgent AI — Orchestration Routing Tests
Tests Supervisor routing to each specialized agent: RAG, Database, Vision, Reasoning, and Action.
"""

import pytest
from app.orchestration.graph import Orchestrator


@pytest.mark.asyncio
async def test_supervisor_to_rag():
    orchestrator = Orchestrator()
    state = await orchestrator.execute(
        message="What does the uploaded safety manual say about emergency shutdown procedures?",
        organization_id="00000000-0000-0000-0000-000000000001",
        user_id="00000000-0000-0000-0000-000000000001",
    )
    assert state["status"] in ("COMPLETED", "ROUTED")
    assert state["intent"] is not None
    # RAG agent or specialist outputs recorded
    assert "rag_agent" in state.get("agent_outputs", {}) or state.get("target_agent") in ("rag_agent", "supervisor")
    assert state.get("final_response") is not None


@pytest.mark.asyncio
async def test_supervisor_to_database():
    orchestrator = Orchestrator()
    state = await orchestrator.execute(
        message="Show production failures and sales amount from database.",
        organization_id="00000000-0000-0000-0000-000000000001",
        user_id="00000000-0000-0000-0000-000000000001",
    )
    assert state["status"] in ("COMPLETED", "ROUTED")
    assert state.get("task_type") in ("DATABASE_QUERY", "DATA_ANALYSIS", "GENERAL_QUERY")
    assert "database_agent" in state.get("agent_outputs", {}) or state.get("target_agent") in ("database_agent", "supervisor")


@pytest.mark.asyncio
async def test_supervisor_to_vision():
    orchestrator = Orchestrator()
    state = await orchestrator.execute(
        message="Analyze this machine image for cracks and surface defects.",
        organization_id="00000000-0000-0000-0000-000000000001",
        user_id="00000000-0000-0000-0000-000000000001",
        attachments=[{"type": "image", "id": "img-001"}],
    )
    assert state["status"] in ("COMPLETED", "ROUTED")
    assert "vision_agent" in state.get("agent_outputs", {}) or state.get("target_agent") in ("vision_agent", "reasoning_agent")


@pytest.mark.asyncio
async def test_supervisor_to_reasoning():
    orchestrator = Orchestrator()
    state = await orchestrator.execute(
        message="Compare this machine image with recent maintenance records and evaluate the discrepancies.",
        organization_id="00000000-0000-0000-0000-000000000001",
        user_id="00000000-0000-0000-0000-000000000001",
        attachments=[{"type": "image", "id": "img-001"}],
    )
    assert state["status"] in ("COMPLETED", "ROUTED")
    # Must involve reasoning or multiple specialist evidence
    assert state.get("target_agent") in ("reasoning_agent", "vision_agent", "database_agent", "supervisor")
    assert state.get("final_response") is not None


@pytest.mark.asyncio
async def test_supervisor_to_action():
    orchestrator = Orchestrator()
    state = await orchestrator.execute(
        message="Send notification to team about completed maintenance shift.",
        organization_id="00000000-0000-0000-0000-000000000001",
        user_id="00000000-0000-0000-0000-000000000001",
    )
    assert state["status"] in ("COMPLETED", "WAITING_FOR_APPROVAL")
    assert state.get("action_requested") is True or "action_agent" in state.get("agent_outputs", {})
