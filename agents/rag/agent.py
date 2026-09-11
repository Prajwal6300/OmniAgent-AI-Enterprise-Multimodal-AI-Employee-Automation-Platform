import time
import uuid
from typing import Any

from agents.rag.citations import CitationBuilder
from agents.rag.context import ContextBuilder
from agents.rag.embeddings import BaseEmbeddingProvider, get_embedding_provider
from agents.rag.graph import build_rag_graph
from agents.rag.nodes import (
    build_citations_node,
    build_context_node,
    filter_context_node,
    generate_answer_node,
    generate_query_embedding_node,
    retrieve_chunks_node,
    validate_grounding_node,
    validate_query_node,
)
from agents.rag.prompts import RAG_FALLBACK_ANSWER
from agents.rag.providers import BaseRAGLLMProvider, get_default_rag_llm_provider
from agents.rag.reranker import BaseReranker, SimpleRelevanceReranker
from agents.rag.retriever import BaseRAGRetriever, InMemoryVectorRetriever
from agents.rag.schemas import Citation, RAGResponse
from agents.rag.state import RAGState

try:
    from app.core.logging import logger
except ImportError:
    try:
        from backend.app.core.logging import logger
    except ImportError:
        import logging
        logger = logging.getLogger("omniagent.rag")


class RAGAgent:
    """
    Enterprise Multimodal AI Employee: Retrieval-Augmented Generation Specialist.
    Executes semantic search over pgvector-indexed enterprise documents, enforces strict
    tenant isolation, defends against prompt injection, prevents hallucination, and generates
    verifiable source citations.
    """

    def __init__(
        self,
        provider: BaseRAGLLMProvider | None = None,
        embedding_provider: BaseEmbeddingProvider | None = None,
        retriever: BaseRAGRetriever | None = None,
        reranker: BaseReranker | None = None,
    ):
        self.provider = provider or get_default_rag_llm_provider()
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.retriever = retriever or InMemoryVectorRetriever()
        self.reranker = reranker or SimpleRelevanceReranker()
        self.context_builder = ContextBuilder()
        self.citation_builder = CitationBuilder()

        self._compiled_graph = build_rag_graph(
            provider=self.provider,
            embedding_provider=self.embedding_provider,
            retriever=self.retriever,
            reranker=self.reranker,
            context_builder=self.context_builder,
            citation_builder=self.citation_builder
        )

    async def query(
        self,
        question: str,
        organization_id: str = "default_org",
        user_id: str | None = None,
        conversation_id: str | None = None,
        document_id: str | None = None,
        top_k: int = 5,
        similarity_threshold: float = 0.05,
        request_id: str | None = None
    ) -> RAGResponse:
        """
        Main entry point for enterprise knowledge retrieval and grounded answer generation.
        Strictly enforces multi-tenant boundary checks.
        """
        start_time = time.time()
        req_id = request_id or str(uuid.uuid4())
        u_id = user_id or "anonymous"
        org_id = str(organization_id)

        initial_state: RAGState = {
            "request_id": req_id,
            "user_id": u_id,
            "organization_id": org_id,
            "conversation_id": conversation_id,
            "question": question,
            "normalized_query": question.strip(),
            "document_id_filter": document_id,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
            "query_embedding": [],
            "filters": {"document_id": document_id} if document_id else {},
            "retrieved_chunks": [],
            "filtered_chunks": [],
            "context": "",
            "raw_answer": "",
            "answer": "",
            "grounded": False,
            "confidence": 0.0,
            "citations": [],
            "retrieved_chunks_count": 0,
            "status": "INITIALIZED",
            "error": None,
            "latency_ms": 0.0
        }

        try:
            if self._compiled_graph is not None:
                final_state = await self._compiled_graph.ainvoke(initial_state)
            else:
                final_state = await self._run_sequential(initial_state)

            latency_ms = round((time.time() - start_time) * 1000, 2)

            # Construct validated Pydantic model
            citations_data = [
                Citation(**c) if isinstance(c, dict) else c
                for c in final_state.get("citations", [])
            ]

            passages = [
                c.get("content", "") if isinstance(c, dict) else getattr(c, "content", "")
                for c in final_state.get("filtered_chunks", [])
            ]

            response = RAGResponse(
                answer=final_state.get("answer", RAG_FALLBACK_ANSWER),
                grounded=final_state.get("grounded", False),
                confidence=final_state.get("confidence", 0.0),
                citations=citations_data,
                retrieved_chunks=final_state.get("retrieved_chunks_count", len(passages)),
                passages=passages,
                query=question,
                latency_ms=latency_ms
            )

            # Structured Audit Logging (execution metadata only, no raw text or token dumps)
            if hasattr(logger, "info"):
                logger.info(
                    "rag_query_completed",
                    request_id=req_id,
                    user_id=u_id,
                    organization_id=org_id,
                    agent_name="rag",
                    grounded=response.grounded,
                    confidence=response.confidence,
                    retrieved_chunks=response.retrieved_chunks,
                    citations_count=len(response.citations),
                    status=final_state.get("status", "SUCCESS"),
                    latency_ms=latency_ms
                )

            return response

        except Exception as exc:  # noqa: BLE001
            latency_ms = round((time.time() - start_time) * 1000, 2)
            if hasattr(logger, "error"):
                logger.error(
                    "rag_query_failed",
                    request_id=req_id,
                    user_id=u_id,
                    organization_id=org_id,
                    error=str(exc),
                    latency_ms=latency_ms
                )

            return RAGResponse(
                answer=RAG_FALLBACK_ANSWER,
                grounded=False,
                confidence=0.0,
                citations=[],
                retrieved_chunks=0,
                passages=[],
                query=question,
                latency_ms=latency_ms
            )

    async def _run_sequential(self, state: RAGState) -> RAGState:
        """Sequential fallback runner if LangGraph compilation is unavailable."""
        current = dict(state)

        # 1. Validate
        u = await validate_query_node(current)
        current.update(u)
        if current.get("status") == "FAILED_VALIDATION":
            u = await build_citations_node(current, builder=self.citation_builder)
            current.update(u)
            return current

        # 2. Embedding
        u = await generate_query_embedding_node(current, provider=self.embedding_provider)
        current.update(u)
        if current.get("status") == "FAILED_EMBEDDING":
            u = await build_citations_node(current, builder=self.citation_builder)
            current.update(u)
            return current

        # 3. Retrieval
        u = await retrieve_chunks_node(current, retriever=self.retriever)
        current.update(u)
        if current.get("status") == "FAILED_RETRIEVAL" or not current.get("retrieved_chunks"):
            # Skip to answer generation (returns fallback)
            u = await generate_answer_node(current, provider=self.provider)
            current.update(u)
            u = await validate_grounding_node(current)
            current.update(u)
            u = await build_citations_node(current, builder=self.citation_builder)
            current.update(u)
            return current

        # 4. Filter & Rerank
        u = await filter_context_node(current, reranker=self.reranker)
        current.update(u)

        # 5. Build Context
        u = await build_context_node(current, builder=self.context_builder)
        current.update(u)

        # 6. Generate Answer
        u = await generate_answer_node(current, provider=self.provider)
        current.update(u)

        # 7. Validate Grounding
        u = await validate_grounding_node(current)
        current.update(u)

        # 8. Build Citations
        u = await build_citations_node(current, builder=self.citation_builder)
        current.update(u)

        return current

    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Legacy/multi-agent graph hook maintaining compatibility with agents/graph/nodes.py.
        """
        question = state.get("task_goal") or state.get("query") or state.get("user_message", "")
        org_id = state.get("organization_id", "default_org")
        doc_id = state.get("document_id")

        if not question:
            return {
                "status": "success",
                "agent": "rag",
                "results": [],
                "passages": [],
                "sources": [],
                "answer": RAG_FALLBACK_ANSWER
            }

        response = await self.query(
            question=question,
            organization_id=org_id,
            document_id=doc_id
        )

        return {
            "status": "success",
            "agent": "rag",
            "results": [c.model_dump() for c in response.citations],
            "passages": response.passages,
            "sources": response.sources,
            "answer": response.answer,
            "grounded": response.grounded,
            "confidence": response.confidence
        }
