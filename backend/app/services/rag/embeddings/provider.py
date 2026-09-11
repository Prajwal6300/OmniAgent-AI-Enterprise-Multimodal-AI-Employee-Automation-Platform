from abc import ABC, abstractmethod
from typing import List

from agents.rag.embeddings import (
    BaseEmbeddingProvider,
    DeterministicEmbeddingProvider,
    MockEmbeddingProvider as AgentMockEmbeddingProvider,
    OpenAIEmbeddingProvider,
    get_embedding_provider,
)


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass


class MockEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    async def embed_query(self, text: str) -> List[float]:
        return [0.0] * self.dimension

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.0] * self.dimension for _ in texts]


class DeterministicBackendEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimension: int = 1536):
        self._provider = DeterministicEmbeddingProvider(dimension=dimension)

    async def embed_query(self, text: str) -> List[float]:
        return await self._provider.embed_query(text)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return await self._provider.embed_documents(texts)
