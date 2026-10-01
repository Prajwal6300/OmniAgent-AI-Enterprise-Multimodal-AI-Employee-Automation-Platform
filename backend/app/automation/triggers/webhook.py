class WebhookTrigger:
    def trigger(self, endpoint: str, headers: dict, body: dict) -> dict:
        return {"trigger_type": "WEBHOOK", "endpoint": endpoint, "payload": body}
