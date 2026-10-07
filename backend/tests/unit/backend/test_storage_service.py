"""
OmniAgent AI — Storage Service Unit Tests
Tests for StorageService wrapper over StorageClient.
"""

import hashlib
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

# Set S3 settings for all S3 storage service tests
from app.core.config import settings as core_settings
from app.services.storage_service import (
    LocalStorageService,
    S3StorageService,
    get_storage_service,
)

core_settings.S3_ENDPOINT = "https://account.r2.cloudflare.com"
core_settings.S3_REGION = "auto"
core_settings.S3_ACCESS_KEY = "access_key"
core_settings.S3_SECRET_KEY = "secret_key"
core_settings.S3_BUCKET = "documents"


def _make_mock_stream(read_data: bytes) -> AsyncMock:
    """Create a mock stream with read() returning the given bytes and async context manager support."""
    mock = AsyncMock()
    mock.read = AsyncMock(return_value=read_data)
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=None)
    return mock


class TestS3StorageServiceSaveFile:
    """Test that S3StorageService.save_file returns relative key and delegates correctly."""

    @patch("app.services.storage_service.S3StorageService._client")
    async def test_save_file_returns_relative_key(self, mock_client_method):
        """save_file should return key in format <org_id>/<uuid>_<name>."""
        # Setup the mock to return an async context manager
        mock_client_return = AsyncMock()
        mock_client_return.__aenter__ = AsyncMock(return_value=mock_client_return)
        mock_client_return.__aexit__ = AsyncMock(return_value=None)
        mock_client_return.put_object = AsyncMock()
        mock_client_method.return_value = mock_client_return

        service = S3StorageService()
        file_data = b"test data"
        original_filename = "test.txt"
        org_id = uuid4()

        key, checksum, size = await service.save_file(
            file_data, original_filename, org_id
        )

        # Key should be relative: <org_id>/<uuid>_<name>
        assert "/" in key
        assert str(org_id) in key
        assert checksum == hashlib.sha256(file_data).hexdigest()
        assert size == len(file_data)

        # Verify put_object was called once with correct arguments
        mock_client_return.put_object.assert_awaited_once()
        call_kwargs = mock_client_return.put_object.call_args
        assert call_kwargs[1]["Bucket"] == service.bucket
        assert call_kwargs[1]["Key"] == key


class TestS3StorageServiceReadFile:
    """Test that S3StorageService.read_file works with mocked StorageClient."""

    @patch("app.services.storage_service.S3StorageService._client")
    async def test_read_file_returns_bytes(self, mock_client_method):
        """read_file should return bytes from StorageClient."""
        # The code does: async with response["Body"] as stream: return await stream.read()
        mock_stream = _make_mock_stream(b"read data")

        mock_client_return = AsyncMock()
        mock_client_return.__aenter__ = AsyncMock(return_value=mock_client_return)
        mock_client_return.__aexit__ = AsyncMock(return_value=None)
        mock_client_return.get_object = AsyncMock(return_value={"Body": mock_stream})
        mock_client_method.return_value = mock_client_return

        service = S3StorageService()
        result = await service.read_file("some/key")

        assert result == b"read data"

        # Verify get_object was called once with correct arguments
        mock_client_return.get_object.assert_awaited_once()
        call_kwargs = mock_client_return.get_object.call_args
        assert call_kwargs[1]["Bucket"] == service.bucket
        assert call_kwargs[1]["Key"] == "some/key"


class TestS3StorageServiceReadFileNotFound:
    """Test that S3StorageService.read_file raises FileNotFoundError when object not found."""

    @patch("app.services.storage_service.S3StorageService._client")
    async def test_read_file_raises_file_not_found(self, mock_client_method):
        """read_file should raise FileNotFoundError when get_object fails."""
        # Setup the mock to raise an exception
        mock_client_return = AsyncMock()
        mock_client_return.__aenter__ = AsyncMock(return_value=mock_client_return)
        mock_client_return.__aexit__ = AsyncMock(return_value=None)
        mock_client_return.get_object = AsyncMock(side_effect=Exception("not found"))
        mock_client_method.return_value = mock_client_return

        service = S3StorageService()

        with pytest.raises(FileNotFoundError, match="S3 storage object not found"):
            await service.read_file("some/key")


class TestS3StorageServiceDeleteFile:
    """Test that S3StorageService.delete_file delegates correctly."""

    @patch("app.services.storage_service.S3StorageService._client")
    async def test_delete_file_returns_true(self, mock_client_method):
        """delete_file should return True when deletion succeeds."""
        # Setup the mock to return an async context manager
        mock_client_return = AsyncMock()
        mock_client_return.__aenter__ = AsyncMock(return_value=mock_client_return)
        mock_client_return.__aexit__ = AsyncMock(return_value=None)
        mock_client_return.delete_object = AsyncMock(return_value=None)
        mock_client_method.return_value = mock_client_return

        service = S3StorageService()
        result = await service.delete_file("some/key")

        assert result is True

        # Verify delete_object was called once
        mock_client_return.delete_object.assert_awaited_once()
        call_kwargs = mock_client_return.delete_object.call_args
        assert call_kwargs[1]["Bucket"] == service.bucket
        assert call_kwargs[1]["Key"] == "some/key"

    @patch("app.services.storage_service.S3StorageService._client")
    async def test_delete_file_returns_false_on_exception(self, mock_client_method):
        """delete_file should return False when deletion fails."""
        # Setup the mock to raise an exception
        mock_client_return = AsyncMock()
        mock_client_return.__aenter__ = AsyncMock(return_value=mock_client_return)
        mock_client_return.__aexit__ = AsyncMock(return_value=None)
        mock_client_return.delete_object = AsyncMock(side_effect=Exception("delete failed"))
        mock_client_method.return_value = mock_client_return

        service = S3StorageService()
        result = await service.delete_file("some/key")

        assert result is False


class TestS3StorageServiceExists:
    """Test that S3StorageService.exists works correctly."""

    @patch("app.services.storage_service.S3StorageService._client")
    async def test_exists_returns_true(self, mock_client_method):
        """exists should return True when object is accessible."""
        # Setup the mock to return an async context manager
        mock_client_return = AsyncMock()
        mock_client_return.__aenter__ = AsyncMock(return_value=mock_client_return)
        mock_client_return.__aexit__ = AsyncMock(return_value=None)
        mock_client_return.head_object = AsyncMock(return_value=None)
        mock_client_method.return_value = mock_client_return

        service = S3StorageService()
        result = await service.exists("some/key")

        assert result is True

        # Verify head_object was called once
        mock_client_return.head_object.assert_awaited_once()
        call_kwargs = mock_client_return.head_object.call_args
        assert call_kwargs[1]["Bucket"] == service.bucket
        assert call_kwargs[1]["Key"] == "some/key"

    @patch("app.services.storage_service.S3StorageService._client")
    async def test_exists_returns_false_when_not_accessible(self, mock_client_method):
        """exists should return False when object is not accessible."""
        # Setup the mock to raise an exception
        mock_client_return = AsyncMock()
        mock_client_return.__aenter__ = AsyncMock(return_value=mock_client_return)
        mock_client_return.__aexit__ = AsyncMock(return_value=None)
        mock_client_return.head_object = AsyncMock(side_effect=Exception("not found"))
        mock_client_method.return_value = mock_client_return

        service = S3StorageService()
        result = await service.exists("some/key")

        assert result is False


class TestGetStorageService:
    """Test the get_storage_service factory."""

    def test_returns_s3_service_when_provider_is_s3(self):
        """get_storage_service('s3') should return S3StorageService."""
        with patch("app.core.config.settings.STORAGE_PROVIDER", "s3"):
            service = get_storage_service("s3")
            assert isinstance(service, S3StorageService)

    def test_returns_local_service_when_provider_is_local(self):
        """get_storage_service('local') should return LocalStorageService."""
        with patch("app.core.config.settings.STORAGE_PROVIDER", "local"):
            service = get_storage_service("local")
            assert isinstance(service, LocalStorageService)

    def test_default_returns_local_in_dev(self):
        """Default should return LocalStorageService in development."""
        with (
            patch("app.core.config.settings.ENVIRONMENT", "development"),
            patch("app.core.config.settings.STORAGE_PROVIDER", "local"),
        ):
            service = get_storage_service()
            assert isinstance(service, LocalStorageService)

class TestStorageServiceAPI:
    """Test that the public API is consistent."""

    @patch("app.services.storage_service.S3StorageService._client")
    async def test_save_file_signature(self, mock_client_method):
        """save_file must have signature (file_data, original_filename, org_id) -> (key, checksum, size)."""
        # Setup the mock to return an async context manager
        mock_client_return = AsyncMock()
        mock_client_return.__aenter__ = AsyncMock(return_value=mock_client_return)
        mock_client_return.__aexit__ = AsyncMock(return_value=None)
        mock_client_return.put_object = AsyncMock()
        mock_client_method.return_value = mock_client_return

        service = S3StorageService()
        file_data = b"data"
        original_filename = "test.txt"
        org_id = UUID("12345678-1234-5678-1234-567812345678")

        result = await service.save_file(file_data, original_filename, org_id)
        assert len(result) == 3
        key, checksum, size = result
        assert isinstance(key, str)
        assert isinstance(checksum, str)
        assert isinstance(size, int)

    @patch("app.services.storage_service.S3StorageService._client")
    async def test_read_file_signature(self, mock_client_method):
        """read_file must have signature (storage_path) -> bytes."""
        # The code does: async with response["Body"] as stream: return await stream.read()
        mock_stream = _make_mock_stream(b"test bytes")

        mock_client_return = AsyncMock()
        mock_client_return.__aenter__ = AsyncMock(return_value=mock_client_return)
        mock_client_return.__aexit__ = AsyncMock(return_value=None)
        mock_client_return.get_object = AsyncMock(return_value={"Body": mock_stream})
        mock_client_method.return_value = mock_client_return

        service = S3StorageService()
        result = await service.read_file("some/key")
        assert isinstance(result, bytes)

    @patch("app.services.storage_service.S3StorageService._client")
    async def test_delete_file_signature(self, mock_client_method):
        """delete_file must have signature (storage_path) -> bool."""
        # Setup the mock to return an async context manager
        mock_client_return = AsyncMock()
        mock_client_return.__aenter__ = AsyncMock(return_value=mock_client_return)
        mock_client_return.__aexit__ = AsyncMock(return_value=None)
        mock_client_return.delete_object = AsyncMock(return_value=None)
        mock_client_method.return_value = mock_client_return

        service = S3StorageService()
        result = await service.delete_file("some/key")
        assert isinstance(result, bool)

    @patch("app.services.storage_service.S3StorageService._client")
    async def test_exists_signature(self, mock_client_method):
        """exists must have signature (storage_path) -> bool."""
        # Setup the mock to return an async context manager
        mock_client_return = AsyncMock()
        mock_client_return.__aenter__ = AsyncMock(return_value=mock_client_return)
        mock_client_return.__aexit__ = AsyncMock(return_value=None)
        mock_client_return.head_object = AsyncMock(return_value=None)
        mock_client_method.return_value = mock_client_return

        service = S3StorageService()
        result = await service.exists("some/key")
        assert isinstance(result, bool)
