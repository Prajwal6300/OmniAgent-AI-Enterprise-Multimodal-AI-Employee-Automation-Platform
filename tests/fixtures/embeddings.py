"""
Test Fixtures: Deterministic Vector Embedding Provider for offline tests.
Uses SHA-256 projections to generate reproducible 1536-dimensional float unit vectors.
Texts sharing vocabulary exhibit genuine cosine similarity.
Does NOT call any external API.
"""

import hashlib
import math


class DeterministicEmbeddingProvider:
    """
    Test fixture: reproducible 1536-d unit vectors for unit tests and CI.
    Strictly isolated to test environments.
    """
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    def _compute_embedding(self, text: str) -> list[float]:
        if not text or not text.strip():
            return [0.0] * self.dimension

        cleaned = text.lower().strip()
        words = cleaned.split()
        vector = [0.0] * self.dimension

        # 1. Word-level hash distribution
        for w in words:
            h = int(hashlib.sha256(w.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if ((h >> 16) % 2 == 0) else -1.0
            vector[idx] += sign * 1.5

        # 2. Substring/character trigram distribution for partial match robustness
        for i in range(max(0, len(cleaned) - 2)):
            tri = cleaned[i:i + 3]
            h = int(hashlib.sha256(tri.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if ((h >> 8) % 2 == 0) else -1.0
            vector[idx] += sign * 0.5

        # 3. L2 Normalization (Euclidean norm to unit vector for cosine distance)
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0.0:
            return [round(v / norm, 6) for v in vector]
        return [0.0] * self.dimension

    async def embed_query(self, text: str) -> list[float]:
        return self._compute_embedding(text)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._compute_embedding(t) for t in texts]
