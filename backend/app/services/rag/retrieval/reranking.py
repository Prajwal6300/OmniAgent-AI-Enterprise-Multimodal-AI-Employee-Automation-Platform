"""
OmniAgent AI — Reranking Service
Production stack is OpenAI API + local heuristic term fusion fallback.
Reranks top 20 hybrid search candidates into top_k final relevant passages.
Supports both synchronous evaluation and asynchronous execution.
"""

from typing import Any

import structlog

from app.agents.rag.reranker import SimpleRelevanceReranker
from app.core.config import settings

logger = structlog.get_logger(__name__)


class AwaitableList(list):
    """Dual sync/async list result allowing transparent `await reranker.rerank()` or `reranker.rerank()`."""

    def __await__(self):
        async def _coro():
            return self

        return _coro().__await__()


class OpenAIReranker:
    """
    OpenAI-powered structured reranker.
    Uses GPT-4o structured JSON relevance scoring with seamless heuristic fallback.
    """

    def __init__(self) -> None:
        self.heuristic_fallback = SimpleRelevanceReranker()

    def rerank(
        self,
        query: str,
        candidate_chunks: list[Any],
        top_k: int = 5,
    ) -> AwaitableList:
        """
        Synchronous/awaitable rerank entrypoint prioritizing low-latency heuristic scoring.
        """
        if not candidate_chunks:
            return AwaitableList([])

        result = self.heuristic_fallback.rerank(query, candidate_chunks, top_k=top_k)
        return AwaitableList(result)

    async def arerank(
        self,
        query: str,
        candidate_chunks: list[Any],
        top_k: int = 5,
    ) -> list[Any]:
        """
        Asynchronous deep LLM structured reranker using OpenAI GPT-4o.
        """
        if not candidate_chunks:
            return []

        if len(candidate_chunks) <= top_k or not settings.OPENAI_API_KEY:
            return self.rerank(query, candidate_chunks, top_k=top_k)

        try:
            import json

            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

            summaries = []
            for i, c in enumerate(candidate_chunks[:20]):
                text = c.content if hasattr(c, "content") else (c.get("content", "") if isinstance(c, dict) else str(c))
                summaries.append(f"[{i}] {text[:300]}")

            prompt = (
                f"Query: {query}\n\n"
                "Evaluate the relevance of each passage to the query on a scale of 0.0 to 1.0.\n"
                "Passages:\n" + "\n\n".join(summaries)
            )

            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a strict relevance reranker. Return JSON with key 'rankings': "
                            "list of objects with 'index' (int) and 'relevance_score' (float 0.0-1.0), "
                            "sorted from most relevant to least relevant."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=500,
            )

            content = response.choices[0].message.content or "{}"
            data = json.loads(content)
            rankings = data.get("rankings", [])

            if rankings:
                ordered_indices = [r["index"] for r in rankings if isinstance(r, dict) and "index" in r]
                reranked = []
                seen_idx = set()
                for idx in ordered_indices:
                    if 0 <= idx < len(candidate_chunks) and idx not in seen_idx:
                        reranked.append(candidate_chunks[idx])
                        seen_idx.add(idx)

                for idx, c in enumerate(candidate_chunks):
                    if idx not in seen_idx:
                        reranked.append(c)

                return reranked[:top_k]

        except Exception as exc:  # noqa: BLE001
            logger.info("openai_rerank_fallback_to_heuristic", error=str(exc))

        return self.rerank(query, candidate_chunks, top_k=top_k)


class Reranker(OpenAIReranker):
    """Production reranker combining OpenAI structured ranking with heuristic fallback."""


def get_reranker() -> Reranker:
    """Factory returning the production reranker."""
    return Reranker()