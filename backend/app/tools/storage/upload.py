from app.tools.storage.client import StorageClient

_client = StorageClient()


async def upload_file(params: dict):
    org_id = params.get("organization_id", "default")
    file_name = params.get("file_name", "upload.bin")
    data = params.get("data", b"")
    if isinstance(data, str):
        data = data.encode("utf-8")
    return await _client.upload(org_id, file_name, data)
