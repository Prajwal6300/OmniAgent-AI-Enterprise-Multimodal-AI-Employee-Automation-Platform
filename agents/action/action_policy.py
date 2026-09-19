"""
OmniAgent AI — Action Agent Action Policy
Maintains policy evaluation and backward compatibility with earlier stubs.
"""

from typing import ClassVar

from agents.action.approval import classify_action_risk, requires_approval
from agents.action.schemas import RiskLevel


class ActionPolicy:
    """Evaluates execution risk and human-in-the-loop approval thresholds."""

    HIGH_RISK_TOOLS: ClassVar[set[str]] = {
        "erp_post_payment",
        "delete_storage_file",
        "send_mass_email",
        "delete_data",
        "financial_change",
        "erp_write",
    }

    def assess_risk(self, tool_name: str, params: dict | None = None) -> str:
        """Assesses risk rating for an action or tool identifier."""
        if tool_name in self.HIGH_RISK_TOOLS:
            return RiskLevel.HIGH.value
        risk = classify_action_risk(tool_name)
        return risk.value

    def is_approval_required(self, tool_name: str, params: dict | None = None) -> bool:
        """Determines if an action requires explicit human authorization."""
        return requires_approval(tool_name, self.assess_risk(tool_name, params))
