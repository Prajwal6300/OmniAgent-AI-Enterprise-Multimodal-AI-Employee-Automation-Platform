from app.tools.storage.client import StorageClient

_client = StorageClient()


async def delete_file(params: dict):
    org_id = params.get("organization_id", "default")
    file_path = params.get("file_path", "")
    deleted = await _client.delete(org_id, file_path)
    return {"deleted": deleted, "file_path": file_path}
