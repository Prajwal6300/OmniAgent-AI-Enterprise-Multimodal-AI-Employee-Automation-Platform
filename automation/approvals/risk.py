class RiskEvaluator:
    def evaluate(self, action_name: str, payload: dict) -> str:
        amount = payload.get("amount", 0.0)
        if amount > 10000.0 or action_name in ["erp_post", "delete_database"]:
            return "HIGH"
        if amount > 1000.0:
            return "MEDIUM"
        return "LOW"
