import math
import pytest
from agents.rag.embeddings import (
    DeterministicEmbeddingProvider,
    MockEmbeddingProvider,
    get_embedding_provider,
)


@pytest.mark.asyncio
async def test_deterministic_embedding_dimension_and_norm():
    provider = DeterministicEmbeddingProvider(dimension=1536)
    vec = await provider.embed_query("What is the company leave policy?")
    assert len(vec) == 1536
    # Check L2 norm is ~1.0
    norm = math.sqrt(sum(v * v for v in vec))
    assert abs(norm - 1.0) < 0.01


@pytest.mark.asyncio
async def test_deterministic_embedding_reproducibility():
    provider = DeterministicEmbeddingProvider(dimension=1536)
    vec1 = await provider.embed_query("Annual vacation policy for employees")
    vec2 = await provider.embed_query("Annual vacation policy for employees")
    assert vec1 == vec2


@pytest.mark.asyncio
async def test_deterministic_embedding_batch_documents():
    provider = DeterministicEmbeddingProvider(dimension=1536)
    docs = [
        "First paragraph about engineering practices.",
        "Second paragraph about finance agreements."
    ]
    batch = await provider.embed_documents(docs)
    assert len(batch) == 2
    assert len(batch[0]) == 1536
    assert len(batch[1]) == 1536
    assert batch[0] != batch[1]


@pytest.mark.asyncio
async def test_deterministic_embedding_semantic_proximity():
    provider = DeterministicEmbeddingProvider(dimension=1536)
    q_vec = await provider.embed_query("company leave policy vacation")
    rel_vec = await provider.embed_query("employees leave policy and annual vacation entitlement")
    unrel_vec = await provider.embed_query("hydraulic machine pressure maintenance lubrication bearing")

    dot_rel = sum(x * y for x, y in zip(q_vec, rel_vec))
    dot_unrel = sum(x * y for x, y in zip(q_vec, unrel_vec))

    # Relevant text must have substantially higher cosine similarity than unrelated text
    assert dot_rel > dot_unrel


@pytest.mark.asyncio
async def test_mock_embedding_provider():
    provider = MockEmbeddingProvider(dimension=1536)
    vec = await provider.embed_query("any query")
    assert len(vec) == 1536
    assert all(v == 0.0 for v in vec)


def test_get_embedding_provider_factory():
    p1 = get_embedding_provider("mock")
    assert isinstance(p1, MockEmbeddingProvider)
    p2 = get_embedding_provider("deterministic")
    assert isinstance(p2, DeterministicEmbeddingProvider)
