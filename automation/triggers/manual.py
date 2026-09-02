class ManualTrigger:
    def trigger(self, user_id: str, payload: dict) -> dict:
        return {"trigger_type": "MANUAL", "triggered_by": user_id, "payload": payload}
