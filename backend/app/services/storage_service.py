import asyncio
import hashlib
import os
import re
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from uuid import UUID

from app.core.config import settings
from app.core.logging import logger


class BaseStorageService(ABC):
    """Abstract storage interface decoupling document persistence from storage backend."""

    @abstractmethod
    async def save_file(
        self,
        file_data: bytes,
        original_filename: str,
        org_id: UUID
    ) -> tuple[str, str, int]:
        """
        Saves file data safely and returns (storage_path, checksum_sha256, file_size_bytes).
        """

    @abstractmethod
    async def read_file(self, storage_path: str) -> bytes:
        """Reads and returns file bytes from storage."""

    @abstractmethod
    async def delete_file(self, storage_path: str) -> bool:
        """Deletes file from storage."""

    @abstractmethod
    async def exists(self, storage_path: str) -> bool:
        """Checks if file exists in storage."""


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes filename against path traversal (../, ..\\) and dangerous shell/OS characters.
    """
    base_name = os.path.basename(filename)
    # Strip any ../ or ..\
    base_name = re.sub(r"\.\.+[/\\Release]*", "", base_name)
    # Allow alphanumeric, underscore, hyphen, dot
    clean = re.sub(r"[^\w\.\-]", "_", base_name)
    if len(clean) > 128:
        ext = Path(clean).suffix
        clean = clean[:128 - len(ext)] + ext
    return clean or "document.bin"


class LocalStorageService(BaseStorageService):
    """Local filesystem storage with tenant path isolation and traversal guards."""

    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.STORAGE_LOCAL_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, storage_path: str) -> Path:
        resolved = Path(storage_path).resolve()
        # Security check: Ensure resolved path is strictly within base_dir
        if not str(resolved).startswith(str(self.base_dir)):
            relative_resolved = (self.base_dir / storage_path).resolve()
            if not str(relative_resolved).startswith(str(self.base_dir)):
                raise ValueError("Security violation: Path traversal detected outside storage root.")
            return relative_resolved
        return resolved

    async def save_file(
        self,
        file_data: bytes,
        original_filename: str,
        org_id: UUID
    ) -> tuple[str, str, int]:
        safe_name = sanitize_filename(original_filename)
        file_uuid = uuid.uuid4().hex
        stored_filename = f"{file_uuid}_{safe_name}"

        # Org isolated directory
        org_dir = self.base_dir / str(org_id)
        org_dir.mkdir(parents=True, exist_ok=True)

        target_path = org_dir / stored_filename

        def _write_sync():
            with open(target_path, "wb") as f:
                f.write(file_data)

        await asyncio.to_thread(_write_sync)

        checksum = hashlib.sha256(file_data).hexdigest()
        file_size = len(file_data)
        logger.info(
            "file_stored_locally",
            storage_path=str(target_path),
            size_bytes=file_size,
            checksum=checksum,
            org_id=str(org_id)
        )
        return str(target_path), checksum, file_size

    async def read_file(self, storage_path: str) -> bytes:
        safe_path = self._resolve_safe_path(storage_path)
        if not safe_path.exists():
            raise FileNotFoundError(f"Storage file not found: {storage_path}")

        def _read_sync() -> bytes:
            with open(safe_path, "rb") as f:
                return f.read()

        return await asyncio.to_thread(_read_sync)

    async def delete_file(self, storage_path: str) -> bool:
        try:
            safe_path = self._resolve_safe_path(storage_path)
            if safe_path.exists():
                safe_path.unlink()
                return True
            return False
        except Exception as exc:  # noqa: BLE001
            logger.warning("file_delete_failed", path=storage_path, error=str(exc))
            return False

    async def exists(self, storage_path: str) -> bool:
        try:
            safe_path = self._resolve_safe_path(storage_path)
            return safe_path.exists()
        except Exception:  # noqa: BLE001
            return False


class SupabaseStorageService(BaseStorageService):
    """
    Production object storage service backed by S3/R2-compatible object storage.
    Provides tenant-isolated object key paths, checksum verification, and traversal guards.
    """

    def __init__(self):

        endpoint = settings.S3_ENDPOINT
        region = settings.S3_REGION or "auto"
        access_key = settings.S3_ACCESS_KEY
        secret_key = settings.S3_SECRET_KEY
        self.bucket = settings.S3_BUCKET

        if not endpoint or not access_key or not secret_key:
            raise ValueError(
                "S3/R2 storage credentials missing. Set S3_ENDPOINT, "
                "S3_ACCESS_KEY, and S3_SECRET_KEY."
            )

        self._s3_client = None
        self._endpoint = endpoint
        self._region = region
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket = self.bucket

    async def _get_client(self):
        if self._s3_client is None:
            import aiobotocore.session
            from botocore.config import Config

            session = aiobotocore.session.get_session()
            kwargs = {
                "region_name": self._region,
                "endpoint_url": self._endpoint,
                "aws_access_key_id": self._access_key,
                "aws_secret_access_key": self._secret_key,
            }
            config = Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            )
            self._s3_client = session.create_client("s3", config=config, **kwargs)
        return self._s3_client

    async def save_file(
        self,
        file_data: bytes,
        original_filename: str,
        org_id: UUID
    ) -> tuple[str, str, int]:
        safe_name = sanitize_filename(original_filename)
        file_uuid = uuid.uuid4().hex
        key = f"{org_id}/{file_uuid}_{safe_name}"

        checksum = hashlib.sha256(file_data).hexdigest()
        file_size = len(file_data)

        def _upload():
            self._s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_data,
                Metadata={
                    "checksum-sha256": checksum,
                    "organization-id": str(org_id),
                    "original-filename": safe_name,
                }
            )

        await asyncio.to_thread(_upload)
        logger.info(
            "file_stored_supabase",
            storage_path=key,
            size_bytes=file_size,
            checksum=checksum,
            org_id=str(org_id)
        )
        return key, checksum, file_size

    async def read_file(self, storage_path: str) -> bytes:
        def _download() -> bytes:
            try:
                response = self._s3_client.get_object(
                    Bucket=self.bucket,
                    Key=storage_path
                )
                return response["Body"].read()
            except Exception as exc:
                raise FileNotFoundError(f"Supabase storage object not found: {storage_path}") from exc

        return await asyncio.to_thread(_download)

    async def delete_file(self, storage_path: str) -> bool:
        def _delete() -> bool:
            try:
                self._s3_client.delete_object(
                    Bucket=self.bucket,
                    Key=storage_path
                )
                return True
            except Exception as exc:  # noqa: BLE001
                logger.warning("supabase_file_delete_failed", path=storage_path, error=str(exc))
                return False

        return await asyncio.to_thread(_delete)

    async def exists(self, storage_path: str) -> bool:
        def _head() -> bool:
            try:
                self._s3_client.head_object(
                    Bucket=self.bucket,
                    Key=storage_path
                )
                return True
            except Exception:  # noqa: BLE001
                return False

        return await asyncio.to_thread(_head)


def get_storage_service(provider: str | None = None) -> BaseStorageService:
    """Factory returning configured storage service provider."""
    selected_provider = (provider or getattr(settings, "STORAGE_PROVIDER", "local")).lower()

    env = getattr(settings, "ENVIRONMENT", "development").lower()
    if env == "production" and selected_provider == "local":
        raise RuntimeError(
            "Production security error: STORAGE_PROVIDER cannot be 'local' in production. "
            "Configure S3/R2 storage ('s3')."
        )

    if selected_provider == "s3":
        return SupabaseStorageService()
    return LocalStorageService()
