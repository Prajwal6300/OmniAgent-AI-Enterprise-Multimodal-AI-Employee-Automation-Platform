"""
OmniAgent AI — Storage Service
Provides unified file storage supporting local filesystem (development)
and S3/R2-compatible object storage (production) with path-traversal guards.
"""

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
from app.tools.storage.client import StorageClient


class BaseStorageService(ABC):
    """Abstract storage interface decoupling document persistence from storage backend."""

    @abstractmethod
    async def save_file(
        self,
        file_data: bytes,
        original_filename: str,
        org_id: UUID,
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
    base_name = re.sub(r"\.\.+[/\\]*", "", base_name)
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
        org_id: UUID,
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
            org_id=str(org_id),
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


class StorageService(BaseStorageService):
    """
    Thin wrapper that delegates to StorageClient from tools/storage/client.py.
    Supports S3/R2 (production) and local filesystem (development) providers.
    """

    def __init__(self, provider: str | None = None, org_id: UUID | str | None = None):
        self.provider = provider or settings.STORAGE_PROVIDER
        self.org_id = org_id
        self.client = StorageClient(provider=self.provider)
        # Use the same base directory as LocalStorageService for local mode
        self.base_dir = Path(settings.STORAGE_LOCAL_DIR).resolve()

    def _resolve_safe_path(self, storage_path: str) -> Path:
        """Enforces path containment within the storage directory."""
        # storage_path format: "org_id/uuid_filename" - split into org dir and filename
        parts = storage_path.split("/", 1)
        org_dir_name = parts[0]
        file_name = parts[1] if len(parts) > 1 else storage_path
        
        org_dir = self.base_dir / org_dir_name
        resolved = org_dir / file_name
        
        # Security check: Ensure resolved path is strictly within base_dir
        if not str(resolved).startswith(str(self.base_dir)):
            raise ValueError("Security violation: Path traversal detected outside storage root.")
        return resolved

    async def save_file(
        self,
        file_data: bytes,
        original_filename: str,
        org_id: UUID,
    ) -> tuple[str, str, int]:
        """Uploads file data to storage via StorageClient and returns (path, checksum, size)."""
        safe_name = sanitize_filename(original_filename)
        file_uuid = uuid.uuid4().hex
        stored_filename = f"{file_uuid}_{safe_name}"
        key = f"{org_id}/{stored_filename}"

        if self.provider == "s3":
            actual_org_id = str(org_id) if self.org_id is None else str(self.org_id)
            result = await self.client.upload(
                organization_id=actual_org_id,
                file_path=key,
                data=file_data,
            )
            # StorageClient.upload returns {"file_path": ..., "provider": ..., "size_bytes": ...}
            # The key we passed is the S3 object key; return the relative path
            file_size = int(result["size_bytes"])
            checksum = hashlib.sha256(file_data).hexdigest()
            return key, checksum, file_size
        else:
            # Local provider - store with relative key path
            return await self._save_file_local(file_data, key, org_id)

    async def _save_file_local(
        self,
        file_data: bytes,
        key: str,
        org_id: UUID,
    ) -> tuple[str, str, int]:
        """Local save logic using a relative key (org_id/uuid_filename)."""
        safe_name = sanitize_filename(key.split("/")[-1])  # extract filename from key
        file_uuid = uuid.uuid4().hex
        stored_filename = f"{file_uuid}_{safe_name}"

        # Store under org directory using the same base dir as LocalStorageService
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
            storage_path=key,  # return the relative key
            size_bytes=file_size,
            checksum=checksum,
            org_id=str(org_id),
        )
        return key, checksum, file_size

    async def read_file(self, storage_path: str) -> bytes:
        """Downloads file data from storage via StorageClient."""
        if self.provider == "s3":
            actual_org_id = str(self.org_id) if self.org_id is not None else "org-unknown"
            return await self.client.download(
                organization_id=actual_org_id,
                file_path=storage_path,
            )
        else:
            # Local provider
            safe_path = self._resolve_safe_path(storage_path)
            if not safe_path.exists():
                raise FileNotFoundError(f"Storage file not found: {storage_path}")

            def _read_sync() -> bytes:
                with open(safe_path, "rb") as f:
                    return f.read()

            return await asyncio.to_thread(_read_sync)

    async def delete_file(self, storage_path: str) -> bool:
        """Deletes file from storage via StorageClient."""
        if self.provider == "s3":
            actual_org_id = str(self.org_id) if self.org_id is not None else "org-unknown"
            return await self.client.delete(
                organization_id=actual_org_id,
                file_path=storage_path,
            )
        else:
            # Local provider
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
        """Checks if file exists in storage."""
        if self.provider == "s3":
            actual_org_id = str(self.org_id) if self.org_id is not None else "org-unknown"
            try:
                await self.client.download(
                    organization_id=actual_org_id,
                    file_path=storage_path,
                )
                return True
            except Exception:  # noqa: BLE001
                return False
        else:
            try:
                safe_path = self._resolve_safe_path(storage_path)
                return safe_path.exists()
            except Exception:  # noqa: BLE001
                return False


def get_storage_service(provider: str | None = None) -> BaseStorageService:
    """Factory returning configured storage service provider."""
    selected_provider = (provider or getattr(settings, "STORAGE_PROVIDER", "local")).lower()

    env = getattr(settings, "ENVIRONMENT", "development").lower()
    if env == "production" and selected_provider == "local":
        raise RuntimeError(
            "Production security error: STORAGE_PROVIDER cannot be 'local' in production. "
            "Configure S3/R2 storage ('s3')."
        )

    return StorageService(provider=selected_provider)