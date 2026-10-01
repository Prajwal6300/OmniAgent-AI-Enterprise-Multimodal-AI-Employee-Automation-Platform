import os
import sys

import pytest

# Ensure backend and modular packages are on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, "backend"))

# Provide test environment variables before app imports
os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-32-chars-long")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-must-be-at-least-32-chars-long")
os.environ.setdefault("ENCRYPTION_KEY", "B1_785eLwHwz0lK91234567890abcdef1234567890=")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/omniagent_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("STORAGE_PROVIDER", "local")

@pytest.fixture
def sample_tenant_id():
    return "00000000-0000-0000-0000-000000000001"


@pytest.fixture(autouse=True)
def setup_test_llm_providers(monkeypatch):
    """Ensures offline test execution uses test fixture doubles without external API calls."""
    import app.agents.rag.agent as rag_agent
    import app.agents.rag.providers as rag_providers
    from app.services.rag.embeddings.factory import EmbeddingFactory
    from tests.fixtures.embeddings import DeterministicEmbeddingProvider
    from tests.fixtures.mock_providers import MockRAGLLMProvider

    monkeypatch.setattr(rag_providers, "get_default_rag_llm_provider", lambda: MockRAGLLMProvider())
    monkeypatch.setattr(rag_agent, "get_default_rag_llm_provider", lambda: MockRAGLLMProvider())
    monkeypatch.setattr(EmbeddingFactory, "get_provider", lambda: DeterministicEmbeddingProvider())


