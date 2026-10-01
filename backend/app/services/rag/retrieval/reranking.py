import asyncio
import os
from typing import List, Any

import numpy as np

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None

try:
    import cohere
except ImportError:
    cohere = None


def _get_reranker_provider() -> str:
    """Get the reranker provider from settings."""
    from app.core.config import settings
    return getattr(settings, "RERANKER_PROVIDER", "cohere").lower()


def _get_cohere_api_key() -> str:
    """Get the Cohere API key from settings or environment."""
    from app.core.config import settings
    key = getattr(settings, "COHERE_API_KEY", "") or os.getenv("COHERE_API_KEY", "")
    return key


def _get_cross_encoder_model() -> str:
    """Get the CrossEncoder model name from settings."""
    from app.core.config import settings
    return getattr(settings, "CROSS_ENCODER_MODEL", "ms-marco-MiniLM-L-6-v2")


class CohereReranker:
    """Cohere Rerank API provider."""

    def __init__(self, api_key: str | None = None, model: str | None = "rerank-english-v3.0"):
        self.api_key = api_key or _get_cohere_api_key()
        self.model = model
        self.client = cohere.Client(self.api_key) if self.api_key else None

    async def rerank(
        self,
        query: str,
        candidate_chunks: list[Any],
        top_k: int = 5,
    ) -> list[Any]:
        """Rerank chunks using Cohere Rerank API.

        Retrieves top 20 from vector search, then reranks to top_k.
        """
        if not self.client:
            raise RuntimeError("Cohere API key not configured. Set COHERE_API_KEY environment variable.")

        # Limit to Cohere's max candidates (typically 100, we'll send top 20)
        chunks_to_rerank = candidate_chunks[:20]

        if not chunks_to_rerank:
            return []

        try:
            response = self.client.rerank(
                query=query,
                documents=[chunk.content for chunk in chunks_to_rerank],
                top_k=min(top_k, len(chunks_to_rerank)),
                model=self.model,
            )

            # Map results back to chunk objects
            reranked_indices = [result.index for result in response.results]
            result_chunks = [chunks_to_rerank[i] for i in reranked_indices]

            # Attach rerank scores
            for i, result in enumerate(response.results):
                if i < len(result_chunks):
                    result_chunks[i].rerank_score = float(result.score)

            return result_chunks[:top_k]

        except Exception as e:
            raise RuntimeError(f"Cohere Rerank failed: {e!s}")


class CrossEncoderReranker:
    """Local sentence-transformers CrossEncoder fallback provider."""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or _get_cross_encoder_model()
        if CrossEncoder is None:
            raise ImportError("sentence-transformers is not installed. Install with: pip install sentence-transformers")
        self.cross_encoder = CrossEncoder(self.model_name)

    async def rerank(
        self,
        query: str,
        candidate_chunks: list[Any],
        top_k: int = 5,
    ) -> list[Any]:
        """Rerank chunks using local CrossEncoder model.

        Retrieves top 20 from vector search, then reranks to top_k.
        """
        if not candidate_chunks:
            return []

        # Limit to reasonable number for CrossEncoder
        chunks_to_rerank = candidate_chunks[:20]

        if not chunks_to_rerank:
            return []

        # Prepare pairs of (query, document_text)
        pairs = [(query, chunk.content) for chunk in chunks_to_rerank]

        # Get similarity scores
        try:
            scores = self.cross_encoder.batch_predict(pairs)
        except Exception as e:
            raise RuntimeError(f"CrossEncoder reranking failed: {e!s}")

        # Sort chunks by score descending
        indexed_chunks = list(enumerate(chunks_to_rerank))
        sorted_chunks = sorted(
            indexed_chunks, key=lambda x: scores[x[0]], reverse=True
        )

        # Return top_k
        result = [chunk for idx, chunk in sorted_chunks[:top_k]]

        # Attach rerank scores
        for i, (idx, _) in enumerate(sorted_chunks[:top_k]):
            if i < len(result):
                result[i].rerank_score = float(scores[idx])

        return result


def get_reranker() -> Any:
    """Factory function to get the configured reranker provider."""
    provider = _get_reranker_provider()

    if provider == "cohere":
        api_key = _get_cohere_api_key()
        if not api_key:
            raise RuntimeError("COHERE_API_KEY not configured. Set COHERE_API_KEY environment variable.")
        return CohereReranker(api_key=api_key)

    if provider == "cross_encoder":
        return CrossEncoderReranker()

    # Default to CrossEncoder fallback
    if CrossEncoder is not None:
        return CrossEncoderReranker()

    raise RuntimeError(
        "No reranker provider configured. Set RERANKER_PROVIDER=cohere with COHERE_API_KEY, "
        "or set RERANKER_PROVIDER=cross_encoder with sentence-transformers installed."
    )