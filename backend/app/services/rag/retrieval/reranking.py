"""
OmniAgent AI — Reranking Service.
Production stack is OpenAI API + local heuristic term fusion.
Cohere and sentence-transformers external rerankers have been removed.
"""

from app.agents.rag.reranker import SimpleRelevanceReranker


class Reranker(SimpleRelevanceReranker):
    """Production reranker combining lexical term frequency with semantic similarity scores."""


def get_reranker() -> Reranker:
    """Factory returning the production reranker."""
    return Reranker()