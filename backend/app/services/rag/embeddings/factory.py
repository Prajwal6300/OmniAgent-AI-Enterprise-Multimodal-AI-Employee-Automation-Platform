from app.services.rag.embeddings.provider import EmbeddingProvider, MockEmbeddingProvider
from app.core.config import settings

class EmbeddingFactory:
    @staticmethod
    def get_provider() -> EmbeddingProvider:
        return MockEmbeddingProvider()
