class ActionPolicy:
    HIGH_RISK_TOOLS = {"erp_post_payment", "delete_storage_file", "send_mass_email"}

    def assess_risk(self, tool_name: str, params: dict) -> str:
        if tool_name in self.HIGH_RISK_TOOLS:
            return "HIGH"
        return "LOW"
