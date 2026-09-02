from agents.vision.schemas import VisionResult

class VisionAgent:
    async def process(self, state: dict) -> dict:
        return {"status": "success", "agent": "vision", "result": "Visual elements analyzed."}
