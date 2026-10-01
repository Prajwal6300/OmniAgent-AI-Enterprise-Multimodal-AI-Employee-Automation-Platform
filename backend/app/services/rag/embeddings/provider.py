from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract interface for RAG vector embedding inference."""

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Embed single query string to float vector."""

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed batch of text chunks to list of float vectors."""
