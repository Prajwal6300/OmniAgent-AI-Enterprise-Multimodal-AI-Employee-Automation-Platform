"""
OmniAgent AI — Embeddings Provider Module.
Production stack is OpenAI API only (text-embedding-3-large, dimensions=1536).
"""

import os
from abc import ABC, abstractmethod

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
    async def embed_query(self, text: str) -> list[float]:
        """Generate vector embedding for a search question."""

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a batch of document chunks."""


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    Real OpenAI vector embedding provider using official AsyncOpenAI SDK.
    Strictly OpenAI API text-embedding-3-large with dimensions=1536.
    """
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "text-embedding-3-large",
        dimension: int = 1536
    ):
        self.api_key = api_key or (getattr(settings, "OPENAI_API_KEY", "") if settings else "") or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self.dimension = dimension
        self._client = None

    def _get_client(self):
        if not self.api_key:
            raise EmbeddingError("OPENAI_API_KEY is not configured. Embeddings require an active OpenAI API key.")
        if not self._client:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise EmbeddingError("The 'openai' package is required for OpenAIEmbeddingProvider.")
        return self._client

    async def embed_query(self, text: str) -> list[float]:
        client = self._get_client()
        try:
            response = await client.embeddings.create(
                input=[text],
                model=self.model,
                dimensions=self.dimension
            )
            return response.data[0].embedding
        except Exception as exc:
            raise EmbeddingError(f"OpenAI embedding generation failed: {exc!s}") from exc

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        client = self._get_client()
        try:
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
    Strictly returns OpenAIEmbeddingProvider. Reports NOT_CONFIGURED honestly when unset.
    """
    api_key = (getattr(settings, "OPENAI_API_KEY", "") if settings else "") or os.getenv("OPENAI_API_KEY", "")
    model = (getattr(settings, "EMBEDDING_MODEL", "text-embedding-3-large") if settings else "text-embedding-3-large")
    dim = (getattr(settings, "EMBEDDING_DIMENSION", 1536) if settings else 1536)
    return OpenAIEmbeddingProvider(api_key=api_key, model=model, dimension=dim)
