from agents.rag.embeddings import OpenAIEmbeddingProvider

from app.core.config import settings


class EmbeddingFactory:
    """Factory creating OpenAI vector embedding providers for RAG ingestion and retrieval."""

    @staticmethod
    def get_provider() -> OpenAIEmbeddingProvider:
        api_key = getattr(settings, "OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not configured. Vector embeddings require a valid OpenAI API key."
            )
        return OpenAIEmbeddingProvider(
            api_key=api_key,
            model=getattr(settings, "EMBEDDING_MODEL", "text-embedding-3-large"),
            dimension=getattr(settings, "EMBEDDING_DIMENSION", 1536),
        )
