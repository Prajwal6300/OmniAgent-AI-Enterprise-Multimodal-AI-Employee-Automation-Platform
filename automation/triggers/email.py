class EmailTrigger:
    def trigger(self, sender: str, subject: str, body: str) -> dict:
        return {"trigger_type": "EMAIL", "sender": sender, "subject": subject}
