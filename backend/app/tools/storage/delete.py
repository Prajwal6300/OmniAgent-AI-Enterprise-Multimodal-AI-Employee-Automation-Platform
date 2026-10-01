async def delete_file(params: dict):
    return {"deleted": True, "key": params.get("key")}
