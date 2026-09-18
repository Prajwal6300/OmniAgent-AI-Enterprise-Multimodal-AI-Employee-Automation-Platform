"""
OmniAgent AI — Reasoning Agent
Primary high-level interface for cross-modal, multi-source grounded reasoning.
Orchestrates specialized downstream agents through LangGraph with strict
tenant isolation, execution limits, conflict detection, and no chain-of-thought exposure.
"""

import time
import uuid
from typing import Any

from agents.reasoning.executor import AgentExecutor, InternalAgentExecutor
from agents.reasoning.graph import build_reasoning_graph, run_sequential_flow
from agents.reasoning.providers import (
    BaseReasoningLLMProvider,
    get_default_reasoning_llm_provider,
)
from agents.reasoning.schemas import (
    Evidence,
    EvidenceConflict,
    ReasoningResponse,
    ReconciliationResult,
)
from agents.reasoning.state import ReasoningState

try:
    from app.core.logging import logger
except ImportError:
    try:
        from backend.app.core.logging import logger
    except ImportError:
        import logging

        logger = logging.getLogger("omniagent.reasoning.agent")


class ReasoningAgent:
    """
    OmniAgent Reasoning Specialist: Enterprise Multimodal AI Employee.
    Coordinates multi-step, multi-agent analytical reasoning across documents,
    tabular databases, visual inspections, and policy knowledge bases.
    """

    def __init__(
        self,
        agent_executor: AgentExecutor | None = None,
        llm_provider: BaseReasoningLLMProvider | None = None,
        max_depth: int = 3,
        max_agent_calls: int = 5,
        timeout_seconds: float = 30.0,
    ):
        self.agent_executor = agent_executor or InternalAgentExecutor(
            default_timeout_seconds=timeout_seconds
        )
        self.llm_provider = llm_provider or get_default_reasoning_llm_provider()
        self.max_depth = max_depth
        self.max_agent_calls = max_agent_calls
        self.timeout_seconds = timeout_seconds

        self._compiled_graph = build_reasoning_graph(
            agent_executor=self.agent_executor,
            llm_provider=self.llm_provider,
            max_depth=self.max_depth,
            max_agent_calls=self.max_agent_calls,
        )

    async def analyze(
        self,
        question: str,
        organization_id: str,
        user_id: str | None = None,
        conversation_id: str | None = None,
        request_id: str | None = None,
        image_id: str | None = None,
        document_id: str | None = None,
        context: dict[str, Any] | None = None,
        depth: int = 0,
    ) -> ReasoningResponse:
        """
        Main cognitive analytical pipeline.
        Executes LangGraph workflow, synthesizing verified evidence without internal chain-of-thought.
        """
        start_time = time.time()
        req_id = request_id or str(uuid.uuid4())
        u_id = user_id or "anonymous"
        c_id = conversation_id or str(uuid.uuid4())
        merged_context = dict(context or {})

        if image_id:
            merged_context["image_id"] = str(image_id)
        if document_id:
            merged_context["document_id"] = str(document_id)

        initial_state: ReasoningState = {
            "request_id": req_id,
            "user_id": u_id,
            "organization_id": str(organization_id),
            "conversation_id": c_id,
            "user_question": question,
            "depth": depth,
            "agent_call_count": 0,
            "context": merged_context,
            "status": "INITIALIZED",
        }

        # Execute compiled LangGraph or fallback sequential flow
        final_state: ReasoningState
        if self._compiled_graph is not None:
            try:
                final_state = await self._compiled_graph.ainvoke(initial_state)
            except Exception as graph_err:  # noqa: BLE001
                logger.warning("reasoning_graph_fallback_invoked", error=str(graph_err))
                final_state = await run_sequential_flow(
                    initial_state=initial_state,
                    agent_executor=self.agent_executor,
                    llm_provider=self.llm_provider,
                    max_depth=self.max_depth,
                    max_agent_calls=self.max_agent_calls,
                )
        else:
            final_state = await run_sequential_flow(
                initial_state=initial_state,
                agent_executor=self.agent_executor,
                llm_provider=self.llm_provider,
                max_depth=self.max_depth,
                max_agent_calls=self.max_agent_calls,
            )

        duration_ms = round((time.time() - start_time) * 1000, 2)

        evidence_models = [Evidence(**e) for e in final_state.get("evidence", [])]
        conflict_models = [
            EvidenceConflict(**c) for c in final_state.get("conflicts", [])
        ]

        return ReasoningResponse(
            answer=final_state.get("answer", "Analysis completed."),
            task_type=final_state.get("task_type", "GENERAL_REASONING"),
            grounded=final_state.get("grounded", True),
            confidence=final_state.get("confidence", 1.0),
            evidence=evidence_models,
            conflicts=conflict_models,
            missing_information=final_state.get("missing_information", []),
            contributing_agents=final_state.get("contributing_agents", []),
            execution_plan=final_state.get("execution_plan", []),
            requires_approval=False,
            latency_ms=duration_ms,
        )

    async def process(self, state: dict) -> dict:
        """Legacy backward compatibility method."""
        return {
            "status": "success",
            "agent": "reasoning",
            "risk_level": "LOW",
            "requires_approval": False,
        }

    async def reconcile(self, state: dict) -> ReconciliationResult:
        """Legacy reconciliation compatibility wrapper."""
        return ReconciliationResult(
            is_matched=True,
            discrepancy_amount=0.0,
            risk_score=0.0,
        )
