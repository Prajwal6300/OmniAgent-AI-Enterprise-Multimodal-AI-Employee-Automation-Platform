from abc import ABC, abstractmethod
from typing import List

class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

class MockEmbeddingProvider(EmbeddingProvider):
    async def embed_query(self, text: str) -> List[float]:
        return [0.0] * 1536

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.0] * 1536 for _ in texts]
