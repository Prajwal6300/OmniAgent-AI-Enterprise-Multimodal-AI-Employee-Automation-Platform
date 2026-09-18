"""
OmniAgent AI — Reasoning Agent Execution Layer
Implements internal agent dispatching, security allowlists, tenant isolation,
timeout handling, and recursion safeguards.
"""

import asyncio
from typing import Any, Protocol, runtime_checkable

from agents.reasoning.exceptions import (
    AgentExecutionTimeoutError,
    RecursionDepthExceededError,
    TenantSecurityViolationError,
    UnsafeAgentCallError,
)

# Strictly authorized specialist agents that the Reasoning Agent is permitted to invoke
ALLOWED_REASONING_AGENTS: set[str] = {
    "document_agent",
    "rag_agent",
    "database_agent",
    "vision_agent",
}

# Explicitly prohibited agent targets to prevent side-effects, recursion, or privilege escalation
PROHIBITED_AGENTS: set[str] = {
    "reasoning_agent",
    "action_agent",
    "email_agent",
    "shell_agent",
    "admin_agent",
    "root_agent",
}


@runtime_checkable
class AgentExecutor(Protocol):
    """Protocol for executing downstream specialist agents."""

    async def execute(
        self,
        agent_name: str,
        request: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Executes an authorized specialist agent with trusted security context.
        Must enforce tenant isolation, timeout safeguards, and strict allowlists.
        """
        ...


class InternalAgentExecutor:
    """
    Direct in-process execution bridge to OmniAgent AI specialist agents.
    Eliminates redundant HTTP hops while enforcing strict tenant boundaries,
    parameter validation, and individual execution timeouts.
    """

    def __init__(
        self,
        database_agent: Any | None = None,
        vision_agent: Any | None = None,
        rag_agent: Any | None = None,
        document_agent: Any | None = None,
        default_timeout_seconds: float = 30.0,
    ):
        self._database_agent = database_agent
        self._vision_agent = vision_agent
        self._rag_agent = rag_agent
        self._document_agent = document_agent
        self.default_timeout_seconds = default_timeout_seconds

    def _get_database_agent(self, context: dict[str, Any]) -> Any:
        if self._database_agent is not None:
            return self._database_agent
        from agents.database.agent import DatabaseAgent

        session = context.get("session")
        return DatabaseAgent(session=session)

    def _get_vision_agent(self) -> Any:
        if self._vision_agent is not None:
            return self._vision_agent
        from agents.vision.agent import VisionAgent

        return VisionAgent()

    def _get_rag_agent(self, context: dict[str, Any]) -> Any:
        if self._rag_agent is not None:
            return self._rag_agent
        from agents.rag.agent import RAGAgent

        session = context.get("session")
        if session:
            from agents.rag.embeddings import get_embedding_provider
            from agents.rag.retriever import DatabaseVectorRetriever

            return RAGAgent(
                embedding_provider=get_embedding_provider(),
                retriever=DatabaseVectorRetriever(session=session),
            )
        return RAGAgent()

    def _get_document_agent(self) -> Any:
        if self._document_agent is not None:
            return self._document_agent
        from agents.document.agent import DocumentAgent

        return DocumentAgent()

    async def execute(
        self,
        agent_name: str,
        request: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        normalized_name = agent_name.strip().lower()

        # 1. Security Check: Recursion Protection
        if normalized_name == "reasoning_agent":
            raise RecursionDepthExceededError(
                "Reasoning Agent cannot invoke itself. Recursive self-invocation is strictly prohibited."
            )

        # 2. Security Check: Allowlist Enforcement
        if (
            normalized_name not in ALLOWED_REASONING_AGENTS
            or normalized_name in PROHIBITED_AGENTS
        ):
            raise UnsafeAgentCallError(
                f"Agent '{agent_name}' is not in the allowed specialist agents list {sorted(ALLOWED_REASONING_AGENTS)}."
            )

        # 3. Mandatory Tenant Isolation Injection
        auth_org_id = context.get("organization_id")
        auth_user_id = context.get("user_id")
        if not auth_org_id:
            raise TenantSecurityViolationError(
                "Missing required authenticated organization_id in context."
            )

        timeout = float(request.get("timeout_seconds") or self.default_timeout_seconds)

        try:
            return await asyncio.wait_for(
                self._dispatch_agent(
                    normalized_name, request, context, auth_org_id, auth_user_id
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            raise AgentExecutionTimeoutError(
                f"Specialist agent '{agent_name}' timed out after {timeout} seconds."
            )

    async def _dispatch_agent(
        self,
        agent_name: str,
        request: dict[str, Any],
        context: dict[str, Any],
        org_id: str,
        user_id: str | None,
    ) -> dict[str, Any]:
        conv_id = context.get("conversation_id")
        req_id = context.get("request_id")

        if agent_name == "database_agent":
            db_agent = self._get_database_agent(context)
            session = context.get("session")
            question = (
                request.get("question")
                or request.get("query")
                or context.get("user_question", "")
            )
            limit = request.get("limit", 50)
            res = await db_agent.query(
                question=question,
                organization_id=str(org_id),
                user_id=str(user_id or "system"),
                limit=limit,
                request_id=req_id,
                conversation_id=conv_id,
                session=session,
            )
            return res.model_dump() if hasattr(res, "model_dump") else dict(res)

        if agent_name == "rag_agent":
            rag_agent = self._get_rag_agent(context)
            question = (
                request.get("question")
                or request.get("query")
                or context.get("user_question", "")
            )
            doc_id = request.get("document_id") or context.get("document_id")
            top_k = request.get("top_k", 5)
            res = await rag_agent.query(
                question=question,
                organization_id=str(org_id),
                user_id=str(user_id or "system"),
                document_id=str(doc_id) if doc_id else None,
                top_k=top_k,
                request_id=req_id,
            )
            return res.model_dump() if hasattr(res, "model_dump") else dict(res)

        if agent_name == "vision_agent":
            vis_agent = self._get_vision_agent()
            image_id = (
                request.get("image_id") or context.get("image_id") or "default_image"
            )
            question = (
                request.get("question")
                or request.get("query")
                or context.get("user_question", "")
            )
            image_bytes = request.get("image_bytes") or context.get("image_bytes")
            image_path = request.get("image_path") or context.get("image_path")
            res = await vis_agent.analyze(
                image_id=str(image_id),
                question=question,
                image_bytes=image_bytes,
                image_path=image_path,
                user_id=str(user_id or "system"),
                organization_id=str(org_id),
                conversation_id=conv_id,
                request_id=req_id,
            )
            return res.model_dump() if hasattr(res, "model_dump") else dict(res)

        if agent_name == "document_agent":
            doc_agent = self._get_document_agent()
            doc_id = (
                request.get("document_id")
                or context.get("document_id")
                or "default_doc"
            )
            task = request.get("task", "summarize")
            query = (
                request.get("query")
                or request.get("question")
                or context.get("user_question")
            )
            file_bytes = request.get("file_bytes") or context.get("file_bytes") or b""
            file_path = request.get("file_path") or context.get("file_path") or ""
            filename = (
                request.get("filename") or context.get("filename") or "document.pdf"
            )
            mime_type = (
                request.get("mime_type")
                or context.get("mime_type")
                or "application/pdf"
            )
            res = await doc_agent.analyze(
                document_id=str(doc_id),
                file_bytes=file_bytes,
                file_path=file_path,
                filename=filename,
                mime_type=mime_type,
                task=task,
                query=query,
                user_id=str(user_id or "system"),
                organization_id=str(org_id),
                request_id=req_id,
            )
            return res.model_dump() if hasattr(res, "model_dump") else dict(res)

        raise UnsafeAgentCallError(f"Unsupported specialist agent '{agent_name}'.")


class MockAgentExecutor:
    """
    Mock agent executor for deterministic offline unit testing, fault injection,
    and partial failure simulations.
    """

    def __init__(
        self,
        agent_responses: dict[str, Any] | None = None,
        simulate_timeout_agents: set[str] | None = None,
        simulate_error_agents: set[str] | None = None,
        simulated_latency: float = 0.0,
    ):
        self.agent_responses = agent_responses or {}
        self.simulate_timeout_agents = simulate_timeout_agents or set()
        self.simulate_error_agents = simulate_error_agents or set()
        self.simulated_latency = simulated_latency
        self.executed_calls: list[dict[str, Any]] = []

    async def execute(
        self,
        agent_name: str,
        request: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        normalized_name = agent_name.strip().lower()

        # Record call for test assertions
        self.executed_calls.append(
            {
                "agent_name": normalized_name,
                "request": request,
                "context": context,
            }
        )

        # Security check: Recursion Protection
        if normalized_name == "reasoning_agent":
            raise RecursionDepthExceededError("Reasoning Agent cannot invoke itself.")

        # Security check: Allowlist
        if (
            normalized_name not in ALLOWED_REASONING_AGENTS
            or normalized_name in PROHIBITED_AGENTS
        ):
            raise UnsafeAgentCallError(f"Agent '{agent_name}' is not in allowed list.")

        # Tenant boundary check
        if not context.get("organization_id"):
            raise TenantSecurityViolationError(
                "Missing required authenticated organization_id in context."
            )

        if self.simulated_latency > 0:
            await asyncio.sleep(self.simulated_latency)

        if normalized_name in self.simulate_timeout_agents:
            raise AgentExecutionTimeoutError(
                f"Agent '{agent_name}' execution timed out."
            )

        if normalized_name in self.simulate_error_agents:
            raise RuntimeError(f"Downstream service outage in '{agent_name}'.")

        if normalized_name in self.agent_responses:
            res = self.agent_responses[normalized_name]
            if isinstance(res, Exception):
                raise res
            return res

        # Deterministic default mock payloads
        if normalized_name == "database_agent":
            return {
                "question": request.get("question", ""),
                "summary": "Database metrics retrieved successfully.",
                "columns": ["id", "status", "count"],
                "rows": [{"id": 1, "status": "active", "count": 10}],
                "row_count": 1,
                "query_executed": True,
                "confidence": 0.95,
            }
        if normalized_name == "rag_agent":
            return {
                "answer": "Relevant knowledge retrieved from company documents.",
                "grounded": True,
                "confidence": 0.94,
                "citations": [
                    {
                        "document_id": "doc-123",
                        "document_name": "Standard Operating Procedure",
                        "page_number": 2,
                        "chunk_id": "chunk-1",
                        "relevance_score": 0.92,
                    }
                ],
                "retrieved_chunks": 1,
            }
        if normalized_name == "vision_agent":
            return {
                "summary": "Visual inspection indicates normal component condition.",
                "answer": "The component shows normal wear without critical damage.",
                "findings": [
                    {
                        "observation": "Component surface intact",
                        "confidence": 0.95,
                        "severity": "info",
                    }
                ],
                "detected_objects": [{"label": "machine_part", "confidence": 0.96}],
                "confidence": 0.95,
            }
        if normalized_name == "document_agent":
            return {
                "title": "Technical Manual",
                "document_type": "TECHNICAL_MANUAL",
                "summary": "Operating procedures and troubleshooting guide.",
                "key_points": ["Inspect component X first upon error."],
                "confidence": 0.96,
                "sources": [{"page": 1, "section": "Troubleshooting"}],
            }

        return {"status": "success", "agent": normalized_name}
