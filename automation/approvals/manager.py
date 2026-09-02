from automation.approvals.policy import ApprovalPolicy
from automation.approvals.risk import RiskEvaluator

class ApprovalManager:
    def __init__(self):
        self.policy = ApprovalPolicy()
        self.risk_eval = RiskEvaluator()

    def check_and_create_gate(self, action_name: str, payload: dict) -> dict:
        risk = self.risk_eval.evaluate(action_name, payload)
        needed = self.policy.requires_approval(action_name, risk, payload.get("amount", 0.0))
        return {
            "requires_approval": needed,
            "risk_level": risk,
            "status": "PENDING_APPROVAL" if needed else "AUTO_APPROVED"
        }
