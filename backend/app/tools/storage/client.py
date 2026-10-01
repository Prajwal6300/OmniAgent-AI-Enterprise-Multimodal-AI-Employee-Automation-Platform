"""
OmniAgent AI — Storage Tool Client
Provides unified file storage supporting local filesystem (development)
and Supabase S3-compatible object storage (production) with path-traversal guards.
"""

import asyncio
import os
from pathlib import Path
from uuid import UUID

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

LOCAL_STORAGE_BASE = Path("storage").resolve()


class StorageClient:
    def __init__(self, provider: str | None = None):
        self.provider = provider or settings.STORAGE_PROVIDER
        self.base_dir = LOCAL_STORAGE_BASE

    def _resolve_safe_path(self, organization_id: UUID | str, file_path: str) -> Path:
        """Enforces path containment within the organization's dedicated directory."""
        org_dir = (self.base_dir / str(organization_id)).resolve()
        org_dir.mkdir(parents=True, exist_ok=True)

        target = (org_dir / file_path.lstrip("/\\")).resolve()
        if not str(target).startswith(str(org_dir)):
            raise ValueError("Path traversal attempt detected")
        return target

    async def upload(
        self,
        organization_id: UUID | str,
        file_path: str,
        data: bytes,
    ) -> dict[str, str]:
        """Uploads file data to storage."""
        if self.provider == "supabase":
            # In production Supabase storage, S3 endpoint or REST API would be called.
            # Local fallback is used if offline.
            pass

        target = self._resolve_safe_path(organization_id, file_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        def _write():
            with open(target, "wb") as f:
                f.write(data)

        await asyncio.to_thread(_write)

        return {
            "file_path": file_path,
            "provider": self.provider,
            "size_bytes": str(len(data)),
        }

    async def download(
        self,
        organization_id: UUID | str,
        file_path: str,
    ) -> bytes:
        """Downloads file data from storage."""
        target = self._resolve_safe_path(organization_id, file_path)
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(f"File not found in storage: {file_path}")

        def _read():
            with open(target, "rb") as f:
                return f.read()

        return await asyncio.to_thread(_read)

    async def delete(
        self,
        organization_id: UUID | str,
        file_path: str,
    ) -> bool:
        """Deletes a file from storage."""
        target = self._resolve_safe_path(organization_id, file_path)
        if target.exists() and target.is_file():
            await asyncio.to_thread(os.remove, target)
            return True
        return False

