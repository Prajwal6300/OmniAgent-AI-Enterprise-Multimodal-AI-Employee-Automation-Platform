from typing import List, Dict, Any

class Reranker:
    def rerank(self, query: str, candidate_chunks: List[Any], top_k: int = 3) -> List[Any]:
        return candidate_chunks[:top_k]
