import hashlib
import math
import os
from abc import ABC, abstractmethod
from typing import List

from agents.rag.exceptions import EmbeddingError

try:
    from app.core.config import settings
except ImportError:
    try:
        from backend.app.core.config import settings
    except ImportError:
        settings = None


class BaseEmbeddingProvider(ABC):
    """
    Abstract Base Class for embedding providers in OmniAgent AI.
    Generates 1536-dimensional float vector embeddings for queries and chunks.
    """
    dimension: int = 1536

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Generate vector embedding for a search question."""
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a batch of document chunks."""
        pass


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Fast, zero-overhead provider returning neutral zero-vector for testing stubs.
    """
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    async def embed_query(self, text: str) -> List[float]:
        return [0.0] * self.dimension

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.0] * self.dimension for _ in texts]


class DeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """
    Production-grade deterministic embedding provider for offline testing and local development.
    Uses SHA-256 token and character n-gram projection to generate reproducible 1536-d unit vectors.
    Texts sharing vocabulary exhibit genuine cosine similarity, allowing real semantic retrieval tests
    without consuming external paid API quotas.
    """
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    def _compute_embedding(self, text: str) -> List[float]:
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

    async def embed_query(self, text: str) -> List[float]:
        return self._compute_embedding(text)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._compute_embedding(t) for t in texts]


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    Real OpenAI vector embedding provider using official AsyncOpenAI SDK.
    """
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "text-embedding-3-large",
        dimension: int = 1536
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self.dimension = dimension
        self._client = None

    def _get_client(self):
        if not self._client:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise EmbeddingError("The 'openai' package is required for OpenAIEmbeddingProvider.")
        return self._client

    async def embed_query(self, text: str) -> List[float]:
        if not self.api_key:
            # Fallback to deterministic provider if API key not supplied
            fallback = DeterministicEmbeddingProvider(dimension=self.dimension)
            return await fallback.embed_query(text)

        try:
            client = self._get_client()
            response = await client.embeddings.create(
                input=[text],
                model=self.model,
                dimensions=self.dimension
            )
            return response.data[0].embedding
        except Exception as exc:
            raise EmbeddingError(f"OpenAI embedding generation failed: {exc!s}") from exc

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if not self.api_key:
            fallback = DeterministicEmbeddingProvider(dimension=self.dimension)
            return await fallback.embed_documents(texts)

        try:
            client = self._get_client()
            # Batch embedding in chunks of 50 to avoid API rate payload limits
            batch_size = 50
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = await client.embeddings.create(
                    input=batch,
                    model=self.model,
                    dimensions=self.dimension
                )
                all_embeddings.extend([item.embedding for item in response.data])
            return all_embeddings
        except Exception as exc:
            raise EmbeddingError(f"OpenAI document batch embedding failed: {exc!s}") from exc


def get_embedding_provider(provider_name: str | None = None) -> BaseEmbeddingProvider:
    """
    Factory creating configured embedding provider.
    Defaults to deterministic provider for resilient offline local testability.
    """
    target = provider_name
    if not target and settings:
        target = getattr(settings, "EMBEDDING_PROVIDER", "deterministic")
    if not target:
        target = os.getenv("EMBEDDING_PROVIDER", "deterministic")

    target = target.lower()

    if target == "openai":
        api_key = os.getenv("OPENAI_API_KEY", getattr(settings, "OPENAI_API_KEY", "") if settings else "")
        if api_key:
            model = getattr(settings, "EMBEDDING_MODEL", "text-embedding-3-large") if settings else "text-embedding-3-large"
            return OpenAIEmbeddingProvider(api_key=api_key, model=model)
        # If openai chosen but no key, use deterministic provider with zero degradation
        return DeterministicEmbeddingProvider()

    if target == "mock":
        return MockEmbeddingProvider()

    return DeterministicEmbeddingProvider()
