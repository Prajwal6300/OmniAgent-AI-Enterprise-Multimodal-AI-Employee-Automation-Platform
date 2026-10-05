"""
OmniAgent AI — Storage Client Unit Tests
Mocked aiobotocore tests proving upload/download/delete are awaited.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.tools.storage.client import StorageClient


@pytest.fixture
def mock_aiobotocore():
    """Mock aiobotocore session and S3 settings so create_client returns an async context manager."""
    with patch("app.tools.storage.client.aiobotocore.session.get_session") as mock_session, \
         patch("app.tools.storage.client.settings.STORAGE_PROVIDER", "s3"), \
         patch("app.tools.storage.client.settings.S3_ENDPOINT", "https://test.endpoint.com"), \
         patch("app.tools.storage.client.settings.S3_BUCKET", "test-bucket"), \
         patch("app.tools.storage.client.settings.S3_ACCESS_KEY", "test-key"), \
         patch("app.tools.storage.client.settings.S3_SECRET_KEY", "test-secret"), \
         patch("app.tools.storage.client.settings.S3_REGION", "us-east-1"):
        mock_client = AsyncMock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_client
        mock_cm.__aexit__.return_value = None
        mock_session.return_value.create_client.return_value = mock_cm
        yield mock_session


@pytest.mark.asyncio
async def test_upload_awaits_put_object(mock_aiobotocore):
    """Upload should await s3_client.put_object directly (no asyncio.to_thread)."""
    client = StorageClient()
    mock_client = mock_aiobotocore.return_value.create_client.return_value.__aenter__.return_value
    mock_client.put_object = AsyncMock(return_value=None)

    result = await client.upload(
        organization_id="org-123",
        file_path="test.txt",
        data=b"hello world",
    )

    assert mock_client.put_object.await_count == 1
    assert result["provider"] == "s3"
    assert result["size_bytes"] == "11"


@pytest.mark.asyncio
async def test_download_awaits_get_object(mock_aiobotocore):
    """Download should await s3_client.get_object directly (no asyncio.to_thread)."""
    client = StorageClient()
    mock_client = mock_aiobotocore.return_value.create_client.return_value.__aenter__.return_value
    mock_body = AsyncMock()
    mock_body.read = AsyncMock(return_value=b"hello world")
    mock_client.get_object = AsyncMock(return_value={"Body": mock_body})

    result = await client.download(
        organization_id="org-123",
        file_path="test.txt",
    )

    assert mock_client.get_object.await_count == 1
    assert result == b"hello world"


@pytest.mark.asyncio
async def test_delete_awaits_delete_object(mock_aiobotocore):
    """Delete should await s3_client.delete_object directly (no asyncio.to_thread)."""
    client = StorageClient()
    mock_client = mock_aiobotocore.return_value.create_client.return_value.__aenter__.return_value

    result = await client.delete(
        organization_id="org-123",
        file_path="test.txt",
    )

    assert mock_client.delete_object.await_count == 1
    assert result is True