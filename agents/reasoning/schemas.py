from pydantic import BaseModel

class ReconciliationResult(BaseModel):
    is_matched: bool
    discrepancy_amount: float = 0.0
    risk_score: float = 0.0
