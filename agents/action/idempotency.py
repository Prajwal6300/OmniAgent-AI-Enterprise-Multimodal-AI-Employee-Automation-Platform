"""
OmniAgent AI — Action Agent Idempotency Manager
Prevents duplicate side-effects across retries, browser refreshes, and network timeouts.
Caches and replays previous ActionResults when matching idempotency keys are supplied.
"""

import asyncio
from datetime import datetime, timezone

from agents.action.schemas import ActionResult


class IdempotencyRecord:
    def __init__(self, key: str, org_id: str, status: str, result: ActionResult | None = None):
        self.key = key
        self.org_id = org_id
        self.status = status  # "IN_PROGRESS", "COMPLETED", "FAILED"
        self.result = result
        self.created_at = datetime.now(timezone.utc)


class IdempotencyManager:
    """Manages idempotency tokens ensuring strict at-most-once side-effect execution."""

    def __init__(self):
        self._store: dict[str, IdempotencyRecord] = {}
        self._lock = asyncio.Lock()

    def _composite_key(self, idempotency_key: str, organization_id: str) -> str:
        return f"{organization_id}:{idempotency_key}"

    async def get(self, idempotency_key: str, organization_id: str) -> ActionResult | None:
        """Retrieves existing completed ActionResult for the given idempotency key."""
        if not idempotency_key:
            return None
        ckey = self._composite_key(idempotency_key, organization_id)
        async with self._lock:
            record = self._store.get(ckey)
            if record and record.result:
                return record.result
        return None

    async def is_in_progress(self, idempotency_key: str, organization_id: str) -> bool:
        """Checks if an identical action execution is currently in progress."""
        if not idempotency_key:
            return False
        ckey = self._composite_key(idempotency_key, organization_id)
        async with self._lock:
            record = self._store.get(ckey)
            return record is not None and record.status == "IN_PROGRESS"

    async def mark_in_progress(self, idempotency_key: str, organization_id: str) -> None:
        """Marks an idempotency token as actively running to block concurrent races."""
        if not idempotency_key:
            return
        ckey = self._composite_key(idempotency_key, organization_id)
        async with self._lock:
            self._store[ckey] = IdempotencyRecord(key=idempotency_key, org_id=organization_id, status="IN_PROGRESS")

    async def record_result(self, idempotency_key: str, organization_id: str, result: ActionResult) -> None:
        """Records final outcome of an executed action under the idempotency key."""
        if not idempotency_key:
            return
        ckey = self._composite_key(idempotency_key, organization_id)
        async with self._lock:
            status = "COMPLETED" if result.success else "FAILED"
            self._store[ckey] = IdempotencyRecord(
                key=idempotency_key, org_id=organization_id, status=status, result=result
            )

    async def clear(self, idempotency_key: str, organization_id: str) -> None:
        """Removes a key from storage (e.g. after clean failure or abort)."""
        if not idempotency_key:
            return
        ckey = self._composite_key(idempotency_key, organization_id)
        async with self._lock:
            self._store.pop(ckey, None)


idempotency_manager = IdempotencyManager()
