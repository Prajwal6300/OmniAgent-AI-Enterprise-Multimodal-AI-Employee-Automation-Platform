from typing import Optional

class LongTermMemory:
    async def recall(self, user_id: str, query: str) -> Optional[str]:
        return None

    async def store(self, user_id: str, key: str, value: str):
        pass
