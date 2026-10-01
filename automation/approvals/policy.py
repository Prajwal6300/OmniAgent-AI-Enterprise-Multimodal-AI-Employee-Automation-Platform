class ApprovalPolicy:
    def requires_approval(self, action_name: str, risk_level: str, amount: float = 0.0) -> bool:
        return bool(risk_level == "HIGH" or amount > 5000.0)
