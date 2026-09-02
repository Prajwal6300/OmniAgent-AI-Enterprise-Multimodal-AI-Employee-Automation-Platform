from agents.rag.retriever import AgentRetriever

class RAGAgent:
    def __init__(self):
        self.retriever = AgentRetriever()

    async def process(self, state: dict) -> dict:
        results = await self.retriever.retrieve(state.get("task_goal", ""))
        return {"status": "success", "agent": "rag", "results": results}
