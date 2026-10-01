async def upload_file(params: dict):
    return {"key": params.get("file_name"), "url": "https://s3.local/bucket/key"}
