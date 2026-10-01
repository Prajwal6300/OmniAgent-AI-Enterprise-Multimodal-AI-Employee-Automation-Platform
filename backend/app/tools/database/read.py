async def read_table(params: dict):
    return {"table": params.get("table"), "records": []}
