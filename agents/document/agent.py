class DocumentAgent:
    async def process(self, state: dict) -> dict:
        return {"status": "success", "agent": "document", "result": "Document structured."}
