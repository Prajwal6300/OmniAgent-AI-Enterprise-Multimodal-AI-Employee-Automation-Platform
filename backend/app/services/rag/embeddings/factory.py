from app.services.rag.embeddings.provider import (
    DeterministicBackendEmbeddingProvider,
    EmbeddingProvider,
    MockEmbeddingProvider,
)
from app.core.config import settings


class EmbeddingFactory:
    @staticmethod
    def get_provider() -> EmbeddingProvider:
        provider_type = getattr(settings, "EMBEDDING_PROVIDER", "mock").lower()
        if provider_type == "deterministic":
            return DeterministicBackendEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)
        if provider_type == "openai" and settings.OPENAI_API_KEY:
            from agents.rag.embeddings import OpenAIEmbeddingProvider
            return OpenAIEmbeddingProvider(api_key=settings.OPENAI_API_KEY, model=settings.EMBEDDING_MODEL)
        return DeterministicBackendEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)
