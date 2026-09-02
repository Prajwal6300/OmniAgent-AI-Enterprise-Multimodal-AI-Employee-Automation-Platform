async def send_email(params: dict):
    return {"recipient": params.get("to"), "status": "sent"}
