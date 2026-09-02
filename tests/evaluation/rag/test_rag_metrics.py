from backend.app.services.rag.retrieval.reranking import Reranker

def test_reranker_evaluation():
    reranker = Reranker()
    res = reranker.rerank("query", ["doc1", "doc2", "doc3"], top_k=2)
    assert len(res) == 2
