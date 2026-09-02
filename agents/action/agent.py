from agents.action.action_policy import ActionPolicy

class ActionAgent:
    def __init__(self):
        self.policy = ActionPolicy()

    async def process(self, state: dict) -> dict:
        risk = self.policy.assess_risk("query_erp", {})
        return {"status": "success", "agent": "action", "risk_assessed": risk}
