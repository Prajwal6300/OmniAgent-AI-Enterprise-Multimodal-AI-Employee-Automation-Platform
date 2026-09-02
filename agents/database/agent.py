from agents.database.sql_guard import SQLGuard

class DatabaseAgent:
    def __init__(self):
        self.guard = SQLGuard()

    async def process(self, state: dict) -> dict:
        return {"status": "success", "agent": "database", "data": []}
