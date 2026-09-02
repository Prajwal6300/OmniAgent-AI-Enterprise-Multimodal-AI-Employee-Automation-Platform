class ScheduleTrigger:
    def trigger(self, schedule_id: str) -> dict:
        return {"trigger_type": "SCHEDULE", "schedule_id": schedule_id}
