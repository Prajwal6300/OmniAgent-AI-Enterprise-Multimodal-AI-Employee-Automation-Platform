from typing import List

class AgentRetriever:
    async def retrieve(self, query: str, top_k: int = 5) -> List[dict]:
        return [{"id": "doc-1", "snippet": "Enterprise standard operating procedure"}]
