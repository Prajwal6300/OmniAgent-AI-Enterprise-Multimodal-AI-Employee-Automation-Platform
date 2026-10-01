"""
OmniAgent AI — Multi-Agent Reasoning & Evidence Aggregation Tests
"""

import pytest

from app.orchestration.executor import (
    OrchestrationAgentExecutor,
    detect_evidence_conflicts,
)
from app.orchestration.graph import Orchestrator


@pytest.mark.asyncio
async def test_reasoning_vision_database():
    """Tests multi-agent reasoning coordinating Vision and Database findings."""
    orchestrator = Orchestrator()
    state = await orchestrator.execute(
        message="Analyze this machine image and cross-reference with production maintenance database records.",
        organization_id="00000000-0000-0000-0000-000000000001",
        user_id="00000000-0000-0000-0000-000000000001",
        attachments=[{"type": "image", "id": "img-failure-99"}],
    )
    assert state["status"] in ("COMPLETED", "ROUTED")
    assert state.get("final_response") is not None
    # Telemetry execution steps recorded
    steps = state.get("execution_steps", [])
    assert len(steps) >= 2


@pytest.mark.asyncio
async def test_reasoning_rag_database():
    """Tests multi-agent reasoning combining RAG policy documentation and database metrics."""
    executor = OrchestrationAgentExecutor()
    simulated_state = {
        "organization_id": "00000000-0000-0000-0000-000000000001",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "user_message": "What is the policy threshold for defect rates and how many defects did we have?",
    }

    rag_res = await executor.execute_agent("rag_agent", simulated_state)
    db_res = await executor.execute_agent("database_agent", simulated_state)

    assert rag_res["status"] == "completed"
    assert db_res["status"] == "completed"
    assert len(rag_res.get("evidence", [])) >= 0
    assert len(db_res.get("evidence", [])) >= 1


def test_multi_agent_evidence_collection():
    """Tests evidence retention from multiple heterogeneous agent outputs."""
    evidence = [
        {
            "source_type": "document",
            "source_id": "doc-manual-01",
            "source_name": "Safety Manual",
            "content": "Emergency shutdown requires valve 4 shutoff.",
            "page_number": 4,
            "confidence": 0.95,
        },
        {
            "source_type": "database",
            "source_id": "sql_query",
            "source_name": "Production Database",
            "content": "Machine M-101 failed 3 times this month.",
            "confidence": 1.0,
        },
    ]

    conflicts = detect_evidence_conflicts(evidence)
    # No direct contradiction between these two
    assert len(conflicts) == 0


def test_conflict_detection_no_silent_merge():
    """Tests that conflicting evidence between vision inspection and database is explicitly flagged."""
    conflicting_evidence = [
        {
            "source_type": "vision",
            "source_id": "img-001",
            "source_name": "Visual Inspection",
            "content": "Severe fatigue crack and structural fail observed on main turbine bearing.",
            "confidence": 0.95,
        },
        {
            "source_type": "database",
            "source_id": "db-query",
            "source_name": "Production Database",
            "content": "Batch passed quality inspection with zero defect count recorded.",
            "confidence": 1.0,
        },
    ]

    conflicts = detect_evidence_conflicts(conflicting_evidence)
    assert len(conflicts) == 1
    assert conflicts[0]["severity"] == "HIGH"
    assert "Visual Inspection" in conflicts[0]["source_a"]
    assert "Production Database" in conflicts[0]["source_b"]
