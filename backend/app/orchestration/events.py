"""
OmniAgent AI — Orchestration Events Layer
Defines structured execution event models, event types, and sanitize logging handlers.
Guarantees zero exposure of API keys, credentials, or internal chain-of-thought.
"""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

try:
    from app.core.logging import logger
except ImportError:
    import logging
    logger = logging.getLogger("omniagent.orchestration.events")


class OrchestrationEventType(str, Enum):
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    SUPERVISOR_STARTED = "SUPERVISOR_STARTED"
    SUPERVISOR_COMPLETED = "SUPERVISOR_COMPLETED"
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_COMPLETED = "AGENT_COMPLETED"
    AGENT_FAILED = "AGENT_FAILED"
    REASONING_STARTED = "REASONING_STARTED"
    REASONING_COMPLETED = "REASONING_COMPLETED"
    ACTION_REQUESTED = "ACTION_REQUESTED"
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    APPROVAL_GRANTED = "APPROVAL_GRANTED"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"
    ACTION_STARTED = "ACTION_STARTED"
    ACTION_COMPLETED = "ACTION_COMPLETED"
    ACTION_VERIFIED = "ACTION_VERIFIED"
    WORKFLOW_PAUSED = "WORKFLOW_PAUSED"
    WORKFLOW_RESUMED = "WORKFLOW_RESUMED"
    REQUEST_COMPLETED = "REQUEST_COMPLETED"
    REQUEST_FAILED = "REQUEST_FAILED"
    REQUEST_CANCELLED = "REQUEST_CANCELLED"


# Sensitive parameter keys to automatically redact
SENSITIVE_KEYS: set[str] = {
    "password", "secret", "token", "authorization", "api_key",
    "apikey", "access_token", "refresh_token", "private_key",
    "jwt", "credentials", "credit_card"
}


def sanitize_event_metadata(data: Any) -> Any:
    """Recursively removes sensitive keys, credentials, and hidden reasoning."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in SENSITIVE_KEYS):
                cleaned[k] = "[REDACTED]"
            elif k_lower in ("thought", "internal_thought", "chain_of_thought", "hidden_reasoning"):
                continue  # Never store hidden chain-of-thought
            else:
                cleaned[k] = sanitize_event_metadata(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_event_metadata(item) for item in data]
    return data


class OrchestrationEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    organization_id: str
    conversation_id: str | None = None
    agent: str | None = None
    event_type: str
    status: str = "INFO"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, context: Any, /) -> None:
        if self.metadata:
            self.metadata = sanitize_event_metadata(self.metadata)


class EventRecorder:
    """Records execution events in memory and safely logs them for observability."""
    def __init__(self):
        self.events: list[OrchestrationEvent] = []

    def record(
        self,
        event_type: OrchestrationEventType | str,
        request_id: str,
        organization_id: str,
        conversation_id: str | None = None,
        agent: str | None = None,
        status: str = "INFO",
        metadata: dict[str, Any] | None = None,
    ) -> OrchestrationEvent:
        e_type = event_type.value if isinstance(event_type, OrchestrationEventType) else str(event_type)
        sanitized_meta = sanitize_event_metadata(metadata or {})
        event = OrchestrationEvent(
            request_id=request_id,
            organization_id=organization_id,
            conversation_id=conversation_id,
            agent=agent,
            event_type=e_type,
            status=status,
            metadata=sanitized_meta,
        )
        self.events.append(event)

        if hasattr(logger, "info"):
            logger.info(
                "orchestration_event",
                event_type=e_type,
                request_id=request_id,
                org_id=organization_id,
                agent=agent,
                status=status,
            )
        return event

    def get_events(self, request_id: str | None = None) -> list[OrchestrationEvent]:
        if request_id:
            return [e for e in self.events if e.request_id == request_id]
        return list(self.events)


# Default singleton instance
event_recorder = EventRecorder()

