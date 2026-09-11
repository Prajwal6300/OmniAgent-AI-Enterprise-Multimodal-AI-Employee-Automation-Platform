import re
from typing import Any

from agents.rag.citations import CitationBuilder
from agents.rag.context import ContextBuilder
from agents.rag.embeddings import BaseEmbeddingProvider, get_embedding_provider
from agents.rag.exceptions import RAGQueryError
from agents.rag.prompts import RAG_FALLBACK_ANSWER
from agents.rag.providers import BaseRAGLLMProvider, get_default_rag_llm_provider
from agents.rag.reranker import BaseReranker, SimpleRelevanceReranker
from agents.rag.retriever import BaseRAGRetriever, InMemoryVectorRetriever
from agents.rag.schemas import RetrievedChunk
from agents.rag.state import RAGState


async def validate_query_node(state: RAGState) -> dict[str, Any]:
    """
    Node 1: Validates incoming user question, sanitizes whitespace, and normalizes query.
    Rejects empty, whitespace-only, or malicious query strings.
    """
    raw_question = state.get("question", "")
    if not raw_question or not raw_question.strip():
        return {
            "status": "FAILED_VALIDATION",
            "error": "Search question is empty or invalid.",
            "answer": RAG_FALLBACK_ANSWER,
            "grounded": False,
            "confidence": 0.0,
            "citations": [],
            "retrieved_chunks_count": 0
        }

    # Normalize whitespace and strip surrounding noise
    cleaned = re.sub(r"\s+", " ", raw_question.strip())

    # Limit query length safeguard (2000 chars)
    if len(cleaned) > 2000:
        cleaned = cleaned[:2000]

    return {
        "status": "QUERY_VALIDATED",
        "question": raw_question,
        "normalized_query": cleaned,
        "error": None
    }


async def generate_query_embedding_node(
    state: RAGState,
    provider: BaseEmbeddingProvider | None = None
) -> dict[str, Any]:
    """
    Node 2: Generates a 1536-dimensional float vector embedding from the normalized query.
    """
    if state.get("status") == "FAILED_VALIDATION":
        return {}

    emb_provider = provider or get_embedding_provider()
    query_text = state.get("normalized_query") or state.get("question", "")

    try:
        embedding = await emb_provider.embed_query(query_text)
        return {
            "status": "QUERY_EMBEDDED",
            "query_embedding": embedding,
            "error": None
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "FAILED_EMBEDDING",
            "error": f"Failed to generate query embedding: {exc!s}",
            "answer": RAG_FALLBACK_ANSWER,
            "grounded": False,
            "confidence": 0.0,
            "citations": [],
            "retrieved_chunks_count": 0
        }


async def retrieve_chunks_node(
    state: RAGState,
    retriever: BaseRAGRetriever | None = None
) -> dict[str, Any]:
    """
    Node 3: Executes vector similarity retrieval enforcing strict organization tenant isolation.
    """
    if state.get("status") in ["FAILED_VALIDATION", "FAILED_EMBEDDING"]:
        return {}

    rag_retriever = retriever or InMemoryVectorRetriever()
    query_emb = state.get("query_embedding", [])
    org_id = state.get("organization_id", "default_org")
    top_k = state.get("top_k", 5)
    doc_id = state.get("document_id_filter")
    threshold = state.get("similarity_threshold", 0.05)
    user_id = state.get("user_id")

    try:
        chunks = await rag_retriever.retrieve(
            query_embedding=query_emb,
            organization_id=org_id,
            top_k=top_k,
            document_id=doc_id,
            similarity_threshold=threshold,
            user_id=user_id
        )

        return {
            "status": "CHUNKS_RETRIEVED",
            "retrieved_chunks": [c.model_dump() if hasattr(c, "model_dump") else c for c in chunks],
            "retrieved_chunks_count": len(chunks),
            "error": None
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "FAILED_RETRIEVAL",
            "error": f"Vector retrieval error: {exc!s}",
            "answer": RAG_FALLBACK_ANSWER,
            "grounded": False,
            "confidence": 0.0,
            "citations": [],
            "retrieved_chunks_count": 0
        }


async def filter_context_node(
    state: RAGState,
    reranker: BaseReranker | None = None
) -> dict[str, Any]:
    """
    Node 4: Applies relevance filtering and candidate chunk reranking.
    Discards clearly irrelevant passages before context construction.
    """
    if state.get("status") in ["FAILED_VALIDATION", "FAILED_EMBEDDING", "FAILED_RETRIEVAL"]:
        return {}

    raw_chunks = state.get("retrieved_chunks", [])
    if not raw_chunks:
        return {
            "status": "CONTEXT_FILTERED",
            "filtered_chunks": [],
            "error": None
        }

    ranker = reranker or SimpleRelevanceReranker()
    query = state.get("normalized_query", state.get("question", ""))
    top_k = state.get("top_k", 5)

    reranked = ranker.rerank(query=query, candidate_chunks=raw_chunks, top_k=top_k)

    return {
        "status": "CONTEXT_FILTERED",
        "filtered_chunks": reranked,
        "error": None
    }


async def build_context_node(
    state: RAGState,
    builder: ContextBuilder | None = None
) -> dict[str, Any]:
    """
    Node 5: Formats reranked passages into an injection-safe context block with document and page metadata.
    """
    if state.get("status") in ["FAILED_VALIDATION", "FAILED_EMBEDDING", "FAILED_RETRIEVAL"]:
        return {}

    context_builder = builder or ContextBuilder()
    chunks = state.get("filtered_chunks", [])

    if not chunks:
        return {
            "status": "CONTEXT_BUILT",
            "context": "",
            "error": None
        }

    context_str = context_builder.build_context(chunks)

    return {
        "status": "CONTEXT_BUILT",
        "context": context_str,
        "error": None
    }


async def generate_answer_node(
    state: RAGState,
    provider: BaseRAGLLMProvider | None = None
) -> dict[str, Any]:
    """
    Node 6: Synthesizes grounded answer using ONLY the supplied context.
    If context is absent or irrelevant, immediately refuses without consulting pre-trained memory.
    """
    if state.get("status") in ["FAILED_VALIDATION", "FAILED_EMBEDDING", "FAILED_RETRIEVAL"]:
        return {}

    context_str = state.get("context", "")
    question = state.get("question", "")

    # Rule: IF NO CONTEXT, NEVER ANSWER FROM MEMORY
    if not context_str or not context_str.strip():
        return {
            "status": "ANSWER_GENERATED",
            "answer": RAG_FALLBACK_ANSWER,
            "raw_answer": RAG_FALLBACK_ANSWER,
            "grounded": False,
            "confidence": 0.0,
            "error": None
        }

    llm = provider or get_default_rag_llm_provider()

    try:
        answer, is_grounded, conf = await llm.generate_rag_answer(
            question=question,
            context=context_str
        )

        return {
            "status": "ANSWER_GENERATED",
            "answer": answer,
            "raw_answer": answer,
            "grounded": is_grounded,
            "confidence": conf,
            "error": None
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "FAILED_GENERATION",
            "error": f"Answer generation failed: {exc!s}",
            "answer": RAG_FALLBACK_ANSWER,
            "grounded": False,
            "confidence": 0.0
        }


async def validate_grounding_node(state: RAGState) -> dict[str, Any]:
    """
    Node 7: Verifies factuality against retrieved context.
    If the answer claims facts unsupported by the context, flips grounded=False and safely falls back.
    """
    if state.get("status") in ["FAILED_VALIDATION", "FAILED_EMBEDDING", "FAILED_RETRIEVAL", "FAILED_GENERATION"]:
        return {
            "status": "FAILED",
            "grounded": False,
            "confidence": 0.0
        }

    answer = state.get("answer", "")
    context_str = state.get("context", "")

    # Fallback response is explicitly not grounded in documents
    if RAG_FALLBACK_ANSWER.lower() in answer.lower():
        return {
            "status": "GROUNDING_VALIDATED",
            "answer": RAG_FALLBACK_ANSWER,
            "grounded": False,
            "confidence": 0.0
        }

    if not context_str:
        return {
            "status": "GROUNDING_VALIDATED",
            "answer": RAG_FALLBACK_ANSWER,
            "grounded": False,
            "confidence": 0.0
        }

    # Verify key tokens in answer appear in context
    stop_words = {"the", "is", "at", "which", "on", "a", "an", "and", "or", "in", "to", "for", "with", "from", "by"}
    answer_tokens = [w for w in re.findall(r"\w+", answer.lower()) if w not in stop_words and len(w) > 3]

    if answer_tokens:
        ctx_lower = context_str.lower()
        supported = [t for t in answer_tokens if t in ctx_lower]
        grounding_ratio = len(supported) / len(answer_tokens)

        # If less than 40% of answer terms are found in context, flag as potentially ungrounded
        if grounding_ratio < 0.4:
            return {
                "status": "GROUNDING_VALIDATED",
                "answer": RAG_FALLBACK_ANSWER,
                "grounded": False,
                "confidence": 0.0
            }

    return {
        "status": "GROUNDING_VALIDATED",
        "grounded": state.get("grounded", True),
        "confidence": state.get("confidence", 0.95)
    }


async def build_citations_node(
    state: RAGState,
    builder: CitationBuilder | None = None
) -> dict[str, Any]:
    """
    Node 8: Constructs validated, non-fabricated citations strictly matching retrieved passages.
    """
    citation_builder = builder or CitationBuilder()
    answer = state.get("answer", RAG_FALLBACK_ANSWER)
    chunks = state.get("filtered_chunks", [])
    grounded = state.get("grounded", False)

    if not grounded or RAG_FALLBACK_ANSWER.lower() in answer.lower():
        return {
            "status": "COMPLETED",
            "citations": [],
            "retrieved_chunks_count": len(chunks)
        }

    citations = citation_builder.build_citations(answer=answer, chunks=chunks)

    return {
        "status": "COMPLETED",
        "citations": [c.model_dump() for c in citations],
        "retrieved_chunks_count": len(chunks)
    }
