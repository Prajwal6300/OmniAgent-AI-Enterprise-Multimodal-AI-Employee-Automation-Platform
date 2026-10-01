from abc import ABC, abstractmethod

from agents.rag.embeddings import (
    DeterministicEmbeddingProvider,
)


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        pass

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        pass


class MockEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    async def embed_query(self, text: str) -> list[float]:
        return [0.0] * self.dimension

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * self.dimension for _ in texts]


class DeterministicBackendEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimension: int = 1536):
        if dimension != 1536:
            raise ValueError(f"Embedding dimension must be 1536, got {dimension}")
        self._provider = DeterministicEmbeddingProvider(dimension=dimension)

    async def embed_query(self, text: str) -> list[float]:
        return await self._provider.embed_query(text)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._provider.embed_documents(texts)
