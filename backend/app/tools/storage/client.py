"""
OmniAgent AI — Storage Tool Client
Provides unified file storage supporting local filesystem (development)
and S3/R2-compatible object storage (production) with path-traversal guards.
"""

import asyncio
import hashlib
import logging
from pathlib import Path
from uuid import UUID

import aiobotocore.session
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

LOCAL_STORAGE_BASE = Path("storage").resolve()


def _build_s3_client():
    """Build an S3 client configured for R2 or any S3-compatible endpoint."""
    endpoint_url = settings.S3_ENDPOINT or None
    region_name = settings.S3_REGION or "auto"
    access_key = settings.S3_ACCESS_KEY or None
    secret_key = settings.S3_SECRET_KEY or None

    if settings.STORAGE_PROVIDER == "s3" and not access_key:
        raise ValueError("S3_ACCESS_KEY is required when STORAGE_PROVIDER is 's3'.")

    session = aiobotocore.session.get_session()
    kwargs = {
        "region_name": region_name,
    }
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    if access_key:
        kwargs["aws_access_key_id"] = access_key
    if secret_key:
        kwargs["aws_secret_access_key"] = secret_key

    # R2 / S3-compatible optimizations: path-style addressing & auto region
    use_path_style = endpoint_url is not None
    if use_path_style:
        kwargs["by_need"] = True  # path-style addressing

    # Configure signature version for S3 compatibility
    from botocore.config import Config
    config = Config(
        signature_version="s3v4",
        s3={
            "addressing_style": "path" if use_path_style else "auto",
        },
    )

    return session.create_client("s3", config=config, **kwargs)


class StorageClient:
    """Unified storage client supporting local and S3/R2 providers."""

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
        if self.provider == "s3":
            endpoint_url = settings.S3_ENDPOINT
            region_name = settings.S3_REGION or "auto"
            access_key = settings.S3_ACCESS_KEY
            secret_key = settings.S3_SECRET_KEY
            bucket = settings.S3_BUCKET

            if not all([endpoint_url, access_key, secret_key, bucket]):
                raise ValueError("S3 endpoint, access key, secret key, and bucket are required for S3 provider.")

            session = aiobotocore.session.get_session()
            kwargs = {
                "region_name": region_name,
                "endpoint_url": endpoint_url,
                "aws_access_key_id": access_key,
                "aws_secret_access_key": secret_key,
            }
            from botocore.config import Config
            config = Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            )

            async with aiobotocore.session.get_session().create_client(
                "s3", config=config, **kwargs
            ) as s3_client:
                safe_name = file_path.lstrip("/\\")
                key = safe_name

                def _upload():
                    s3_client.put_object(
                        Bucket=bucket,
                        Key=key,
                        Body=data,
                        Metadata={
                            "checksum-sha256": hashlib.sha256(data).hexdigest(),
                            "organization-id": str(organization_id),
                        },
                    )

                await asyncio.to_thread(_upload)
                logger.info(
                    "file_stored_s3",
                    key=key,
                    bucket=bucket,
                    organization_id=str(organization_id),
                    size_bytes=len(data),
                )
                return {
                    "file_path": file_path,
                    "provider": "s3",
                    "size_bytes": str(len(data)),
                }
        else:
            # Local filesystem fallback
            target = self._resolve_safe_path(organization_id, file_path)
            target.parent.mkdir(parents=True, exist_ok=True)

            def _write():
                with open(target, "wb") as f:
                    f.write(data)

            await asyncio.to_thread(_write)
            return {
                "file_path": file_path,
                "provider": "local",
                "size_bytes": str(len(data)),
            }

    async def download(
        self,
        organization_id: UUID | str,
        file_path: str,
    ) -> bytes:
        """Downloads file data from storage."""
        if self.provider == "s3":
            endpoint_url = settings.S3_ENDPOINT
            bucket = settings.S3_BUCKET

            if not all([endpoint_url, bucket]):
                raise ValueError("S3 endpoint and bucket are required for S3 provider.")

            session = aiobotocore.session.get_session()
            kwargs = {
                "region_name": settings.S3_REGION or "auto",
                "endpoint_url": endpoint_url,
                "aws_access_key_id": settings.S3_ACCESS_KEY,
                "aws_secret_access_key": settings.S3_SECRET_KEY,
            }
            from botocore.config import Config
            config = Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            )

            async with aiobotocore.session.get_session().create_client(
                "s3", config=config, **kwargs
            ) as s3_client:
                def _download():
                    response = s3_client.get_object(
                        Bucket=bucket,
                        Key=file_path.lstrip("/\\"),
                    )
                    return response["Body"].read()

                return await asyncio.to_thread(_download)
        else:
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
        if self.provider == "s3":
            endpoint_url = settings.S3_ENDPOINT
            bucket = settings.S3_BUCKET

            if not all([endpoint_url, bucket]):
                raise ValueError("S3 endpoint and bucket are required for S3 provider.")

            session = aiobotocore.session.get_session()
            kwargs = {
                "region_name": settings.S3_REGION or "auto",
                "endpoint_url": endpoint_url,
                "aws_access_key_id": settings.S3_ACCESS_KEY,
                "aws_secret_access_key": settings.S3_SECRET_KEY,
            }
            from botocore.config import Config
            config = Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            )

            async with aiobotocore.session.get_session().create_client(
                "s3", config=config, **kwargs
            ) as s3_client:
                def _delete():
                    s3_client.delete_object(
                        Bucket=bucket,
                        Key=file_path.lstrip("/\\"),
                    )
                    return True

                return await asyncio.to_thread(_delete)
        else:
            target = self._resolve_safe_path(organization_id, file_path)
            if target.exists() and target.is_file():
                await asyncio.to_thread(os.remove, target)
                return True
            return False