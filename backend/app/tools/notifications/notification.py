async def send_notification(params: dict):
    return {"channel": params.get("channel"), "status": "dispatched"}
