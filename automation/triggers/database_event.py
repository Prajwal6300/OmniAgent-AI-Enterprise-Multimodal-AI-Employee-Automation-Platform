class DatabaseEventTrigger:
    def trigger(self, table: str, operation: str, record_id: str) -> dict:
        return {"trigger_type": "DATABASE_EVENT", "table": table, "operation": operation, "id": record_id}
