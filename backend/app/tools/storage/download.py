from app.tools.storage.client import StorageClient

_client = StorageClient()


async def download_file(params: dict):
    org_id = params.get("organization_id", "default")
    file_path = params.get("file_path", "")
    return await _client.download(org_id, file_path)
