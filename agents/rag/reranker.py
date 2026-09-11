"""
Reranking Engine for OmniAgent AI RAG System.

STATUS: PARTIALLY IMPLEMENTED
A high-efficiency heuristic and lexical term-frequency reranker is implemented.
The interface is designed to support deep neural cross-encoder models (e.g. Cohere, BGE-Reranker)
without breaking existing pipeline contracts.
"""

from abc import ABC, abstractmethod
from typing import Any, List
import re


class BaseReranker(ABC):
    """Abstract base class for chunk reranking."""

    @abstractmethod
    def rerank(self, query: str, candidate_chunks: List[Any], top_k: int = 5) -> List[Any]:
        """Rerank candidate chunks according to query relevance."""
        pass


class SimpleRelevanceReranker(BaseReranker):
    """
    Production-safe, low-latency heuristic reranker.
    Computes lexical intersection, exact token match density, and weights against
    initial vector similarity to prioritize high-precision passages.
    """

    def rerank(self, query: str, candidate_chunks: List[Any], top_k: int = 5) -> List[Any]:
        if not candidate_chunks:
            return []

        query_terms = set(re.findall(r"\w+", query.lower()))
        if not query_terms:
            return candidate_chunks[:top_k]

        scored_candidates = []
        for c in candidate_chunks:
            c_dict = c if isinstance(c, dict) else (c.model_dump() if hasattr(c, "model_dump") else {"content": str(c)})
            content = c_dict.get("content", "").lower()

            # 1. Base vector score
            base_score = float(c_dict.get("similarity_score", 0.5))

            # 2. Term overlap ratio
            matched_terms = sum(1 for term in query_terms if term in content)
            overlap_ratio = matched_terms / max(1, len(query_terms))

            # 3. Exact phrase match bonus
            phrase_bonus = 0.2 if query.lower() in content else 0.0

            # Composite final score
            final_score = (base_score * 0.5) + (overlap_ratio * 0.4) + phrase_bonus

            # Update score if it's a dict or model
            if isinstance(c, dict):
                c["similarity_score"] = round(final_score, 4)
            elif hasattr(c, "similarity_score"):
                c.similarity_score = round(final_score, 4)

            scored_candidates.append((final_score, c))

        # Sort descending by composite score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_candidates[:top_k]]


# Backward compatibility alias
class AgentReranker(SimpleRelevanceReranker):
    pass
