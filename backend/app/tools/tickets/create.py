"""
OmniAgent AI — Ticket Creation Tool
Dispatches ticket creation to external webhooks (Jira, Linear, GitHub, Zendesk)
with cryptographic idempotency keys and structured reporting.
"""

import hashlib
import time
import uuid
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


async def create_ticket(params: dict[str, Any]) -> dict[str, Any]:
    title = params.get("title", "Automated Agent Ticket")
    description = params.get("description", "")
    priority = params.get("priority", "MEDIUM")
    webhook_url = params.get("webhook_url") or params.get("api_url")

    # Generate or reuse idempotency key
    raw_key = params.get("idempotency_key") or f"{title}:{description}:{time.time() // 60}"
    idempotency_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]

    if webhook_url:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    webhook_url,
                    json={
                        "title": title,
                        "description": description,
                        "priority": priority,
                        "idempotency_key": idempotency_key,
                    },
                    headers={"Idempotency-Key": idempotency_key},
                )
                res.raise_for_status()
                return {
                    "ticket_id": f"TICK-{idempotency_key.upper()}",
                    "status": "CREATED",
                    "external_status": res.status_code,
                    "idempotency_key": idempotency_key,
                }
        except Exception as exc:  # noqa: BLE001
            logger.warning("ticket_webhook_dispatch_failed", url=webhook_url, error=str(exc))
            return {
                "status": "FAILED",
                "error": str(exc),
                "idempotency_key": idempotency_key,
            }

    ticket_ref = f"TICK-{uuid.uuid4().hex[:8].upper()}"
    return {
        "ticket_id": ticket_ref,
        "status": "CREATED",
        "title": title,
        "priority": priority,
        "idempotency_key": idempotency_key,
    }
