"""
OmniAgent AI — Redis Client & Distributed Concurrency Controls
Provides async Redis client management, distributed locking, and token revocation.
Gracefully falls back to an in-memory async coordinator during offline testing.
"""

import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# In-memory storage for test/offline fallback
_in_memory_kv: dict[str, tuple[str, float | None]] = {}
_in_memory_locks: dict[str, str] = {}


class InMemoryRedis:
    """Thread-safe / asyncio in-memory double for environments without Redis server."""

    def __init__(self) -> None:
        self.kv = _in_memory_kv
        self.locks = _in_memory_locks

    def _cleanup_expired(self) -> None:
        now = time.monotonic()
        expired = [k for k, (_, exp) in self.kv.items() if exp is not None and exp < now]
        for k in expired:
            self.kv.pop(k, None)

    async def set(
        self,
        name: str,
        value: Any,
        ex: int | None = None,
        nx: bool = False,
    ) -> bool:
        self._cleanup_expired()
        now = time.monotonic()
        expiry = (now + ex) if ex is not None else None

        if nx and name in self.kv:
            _existing_val, existing_exp = self.kv[name]
            if existing_exp is None or existing_exp > now:
                return False

        self.kv[name] = (str(value), expiry)
        return True

    async def get(self, name: str) -> str | None:
        self._cleanup_expired()
        item = self.kv.get(name)
        if not item:
            return None
        val, expiry = item
        if expiry is not None and expiry < time.monotonic():
            self.kv.pop(name, None)
            return None
        return val

    async def delete(self, *names: str) -> int:
        count = 0
        for name in names:
            if self.kv.pop(name, None):
                count += 1
        return count

    async def exists(self, *names: str) -> int:
        self._cleanup_expired()
        count = 0
        for name in names:
            if name in self.kv:
                count += 1
        return count


# Singleton client holder
_redis_instance = None


def get_redis_client():
    """Returns configured async Redis client or in-memory fallback."""
    global _redis_instance
    if _redis_instance is not None:
        return _redis_instance

    if getattr(settings, "ENVIRONMENT", "") == "test":
        _redis_instance = InMemoryRedis()
        return _redis_instance

    try:
        import redis.asyncio as aioredis  # type: ignore[import-untyped]
        _redis_instance = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
        )
    except Exception as exc:  # noqa: BLE001
        logger.info("using_in_memory_redis_fallback", reason=str(exc))
        _redis_instance = InMemoryRedis()

    return _redis_instance


@asynccontextmanager
async def distributed_lock(
    lock_key: str,
    timeout_seconds: int = 10,
    retry_delay: float = 0.05,
    max_retries: int = 40,
) -> AsyncIterator[str]:
    """
    Acquires an exclusive distributed lock across workers for a critical section.
    Raises TimeoutError if lock cannot be acquired within retry budget.
    """
    import asyncio
    client = get_redis_client()
    lock_token = str(uuid.uuid4())
    acquired = False

    for _ in range(max_retries):
        try:
            # Set key if Not eXists with expiration
            ok = await client.set(f"lock:{lock_key}", lock_token, ex=timeout_seconds, nx=True)
            if ok:
                acquired = True
                break
        except Exception as exc:  # noqa: BLE001
            logger.debug("distributed_lock_retry", key=lock_key, error=str(exc))
        await asyncio.sleep(retry_delay)

    if not acquired:
        raise TimeoutError(f"Could not acquire distributed lock for key: {lock_key}")

    try:
        yield lock_token
    finally:
        try:
            curr = await client.get(f"lock:{lock_key}")
            if curr == lock_token:
                await client.delete(f"lock:{lock_key}")
        except Exception as exc:  # noqa: BLE001
            logger.warning("failed_releasing_distributed_lock", key=lock_key, error=str(exc))


async def revoke_token(token_identifier: str, expires_in_seconds: int = 86400) -> None:
    """Marks a token or JTI as revoked in Redis."""
    client = get_redis_client()
    try:
        await client.set(f"revoked_token:{token_identifier}", "1", ex=expires_in_seconds)
    except Exception as exc:  # noqa: BLE001
        logger.error("failed_revoking_token", identifier=token_identifier, error=str(exc))


async def is_token_revoked(token_identifier: str) -> bool:
    """Checks whether a token or JTI has been revoked."""
    client = get_redis_client()
    try:
        res = await client.get(f"revoked_token:{token_identifier}")
        return res is not None
    except Exception as exc:  # noqa: BLE001
        logger.error("failed_checking_token_revocation", identifier=token_identifier, error=str(exc))
        return False
