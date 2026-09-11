import time
import uuid
from typing import Any

from agents.supervisor.graph import build_supervisor_graph
from agents.supervisor.nodes import (
    classify_intent_node,
    create_task_plan_node,
    determine_capability_node,
    determine_risk_node,
    select_agent_node,
    validate_decision_node,
    validate_request_node,
)
from agents.supervisor.providers import BaseLLMProvider, get_default_llm_provider
from agents.supervisor.router import create_fallback_decision
from agents.supervisor.schemas import AgentTarget, SupervisorDecision, TaskType
from agents.supervisor.state import SupervisorState

try:
    from app.core.logging import logger
except ImportError:
    try:
        from backend.app.core.logging import logger
    except ImportError:
        import logging
        logger = logging.getLogger("omniagent.supervisor")


class SupervisorAgent:
    """
    Central cognitive orchestrator for OmniAgent AI.
    Analyzes requests, classifies enterprise tasks, maps capabilities to specialized agents,
    evaluates execution risks, and produces operational plans.
    """

    def __init__(
        self,
        model_name: str = "gpt-4o",
        provider: BaseLLMProvider | None = None
    ):
        self.model_name = model_name
        self.provider = provider or get_default_llm_provider()
        self._compiled_graph = build_supervisor_graph(provider=self.provider)

    async def analyze(
        self,
        message: str,
        conversation_id: str | None = None,
        user_id: str | None = None,
        organization_id: str | None = None,
        request_id: str | None = None,
        context: dict[str, Any] | None = None
    ) -> SupervisorDecision:
        """
        Main entry point to analyze a natural language user request.
        Executes the LangGraph pipeline with resilience, latency tracking,
        and structured audit logging.
        """
        start_time = time.time()
        req_id = request_id or str(uuid.uuid4())
        u_id = user_id or "anonymous"
        org_id = organization_id or "default_org"
        conv_id = conversation_id or str(uuid.uuid4())

        initial_state: SupervisorState = {
            "request_id": req_id,
            "user_id": u_id,
            "organization_id": org_id,
            "conversation_id": conv_id,
            "user_message": message,
            "context": context or {},
            "status": "INITIALIZED",
            "error": None,
            "confidence": 0.0,
            "task_plan": [],
            "requires_tool": False,
            "requires_approval": False
        }

        try:
            if self._compiled_graph is not None:
                # Execute compiled LangGraph workflow
                final_state = await self._compiled_graph.ainvoke(initial_state)
            else:
                # Sequential node execution fallback if LangGraph is not compiled
                final_state = await self._run_sequential(initial_state)

            total_latency_ms = round((time.time() - start_time) * 1000, 2)
            final_decision = SupervisorDecision(
                intent=final_state.get("intent", "unknown"),
                task_type=final_state.get("task_type", TaskType.UNKNOWN.value),
                capability=final_state.get("capability", "unknown"),
                selected_agent=final_state.get("selected_agent", AgentTarget.SUPERVISOR.value),
                priority=final_state.get("priority", "medium"),
                confidence=final_state.get("confidence", 0.0),
                requires_tool=final_state.get("requires_tool", False),
                requires_approval=final_state.get("requires_approval", False),
                task_plan=final_state.get("task_plan", []),
                explanation=final_state.get("explanation", "")
            )

            # Audit logging: execution metadata only, no tokens or sensitive docs
            if hasattr(logger, "info"):
                logger.info(
                    "supervisor_analysis_completed",
                    request_id=req_id,
                    user_id=u_id,
                    organization_id=org_id,
                    conversation_id=conv_id,
                    agent_name="supervisor",
                    execution_time=total_latency_ms,
                    status=final_state.get("status", "SUCCESS"),
                    selected_agent=final_decision.selected_agent,
                    confidence=final_decision.confidence,
                    task_type=final_decision.task_type,
                    requires_approval=final_decision.requires_approval
                )

            return final_decision

        except Exception as exc:  # noqa: BLE001
            total_latency_ms = round((time.time() - start_time) * 1000, 2)
            if hasattr(logger, "error"):
                logger.error(
                    "supervisor_analysis_failed",
                    request_id=req_id,
                    user_id=u_id,
                    organization_id=org_id,
                    conversation_id=conv_id,
                    error=str(exc),
                    execution_time=total_latency_ms
                )
            return create_fallback_decision(
                explanation="An unexpected error occurred during request analysis.",
                error=str(exc)
            )

    async def _run_sequential(self, state: SupervisorState) -> SupervisorState:
        """Fallback runner executing individual nodes sequentially."""
        current = dict(state)
        # 1. Validate
        update = await validate_request_node(current)
        current.update(update)
        if current.get("status") == "FAILED_VALIDATION":
            val_update = await validate_decision_node(current)
            current.update(val_update)
            return current

        # 2. Classify
        update = await classify_intent_node(current, provider=self.provider)
        current.update(update)

        # 3. Capability
        update = await determine_capability_node(current)
        current.update(update)

        # 4. Agent
        update = await select_agent_node(current)
        current.update(update)

        # 5. Risk
        update = await determine_risk_node(current)
        current.update(update)

        # 6. Plan
        update = await create_task_plan_node(current)
        current.update(update)

        # 7. Final Validate
        update = await validate_decision_node(current)
        current.update(update)

        return current

    async def evaluate_step(self, state: dict) -> SupervisorDecision:
        """
        Legacy method maintaining full backward compatibility with
        tests/unit/agents/test_supervisor.py and agents/graph/nodes.py.
        """
        intermediate_steps = state.get("intermediate_steps", [])
        task_goal = state.get("task_goal") or state.get("user_message", "")

        if intermediate_steps:
            # Task is already in progress and specialist returned
            return SupervisorDecision(
                intent="task_completion",
                task_type=TaskType.GENERAL_QUERY.value,
                capability="completion",
                selected_agent=AgentTarget.SUPERVISOR.value,
                priority="low",
                confidence=1.0,
                requires_tool=False,
                requires_approval=False,
                task_plan=[],
                explanation="Task fulfilled by specialists.",
                next_agent="end",
                is_task_complete=True
            )

        # Initial evaluation
        if task_goal:
            return await self.analyze(message=task_goal)

        return create_fallback_decision(explanation="No task goal provided.")

    async def run_document_agent(
        self,
        document_id: str,
        file_bytes: bytes | None = None,
        file_path: str | None = None,
        filename: str = "document.bin",
        task: str = "summarize",
        query: str | None = None,
        user_id: str | None = None,
        organization_id: str | None = None,
        request_id: str | None = None,
    ):
        """
        Directly delegates execution to the Document Agent for document-related tasks.
        Returns DocumentAnalysisResult or raises DocumentProcessingError.
        """
        from agents.document.agent import DocumentAgent
        from agents.document.exceptions import DocumentProcessingError
        try:
            doc_agent = DocumentAgent()
            return await doc_agent.analyze(
                document_id=document_id,
                file_bytes=file_bytes,
                file_path=file_path,
                filename=filename,
                task=task,
                query=query,
                user_id=user_id,
                organization_id=organization_id,
                request_id=request_id
            )
        except Exception as exc:
            raise DocumentProcessingError(f"Document Agent execution failed: {str(exc)}")

    async def run_rag_agent(
        self,
        question: str,
        document_id: str | None = None,
        user_id: str | None = None,
        organization_id: str | None = None,
        conversation_id: str | None = None,
        top_k: int = 5,
        request_id: str | None = None,
        retriever=None
    ):
        """
        Directly delegates execution to the RAG Agent for knowledge search tasks.
        Returns RAGResponse or raises RAGException.
        """
        from agents.rag.agent import RAGAgent
        from agents.rag.exceptions import RAGException
        try:
            rag_agent = RAGAgent(retriever=retriever)
            return await rag_agent.query(
                question=question,
                document_id=document_id,
                user_id=user_id,
                organization_id=organization_id or "default_org",
                conversation_id=conversation_id,
                top_k=top_k,
                request_id=request_id
            )
        except Exception as exc:
            raise RAGException(f"RAG Agent execution failed: {str(exc)}")

