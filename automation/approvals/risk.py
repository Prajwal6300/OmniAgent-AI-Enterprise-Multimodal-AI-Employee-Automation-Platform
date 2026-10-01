class RiskEvaluator:
    def evaluate(self, action_name: str, payload: dict) -> str:
        amount = payload.get("amount", 0.0)
        if amount > 10000.0 or action_name in ["financial_change", "delete_database", "delete_data"]:
            return "HIGH"
        if amount > 1000.0:
            return "MEDIUM"
        return "LOW"
