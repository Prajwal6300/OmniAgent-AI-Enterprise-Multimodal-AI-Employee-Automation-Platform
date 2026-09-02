async def update_ticket(params: dict):
    return {"ticket_id": params.get("ticket_id"), "status": "UPDATED"}
