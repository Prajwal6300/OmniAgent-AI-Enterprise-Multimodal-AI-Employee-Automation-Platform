"""
OmniAgent AI — Automation Triggers
Clean abstraction layer for MANUAL, EVENT, and SCHEDULE workflow triggers.
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any


class Trigger(ABC):
    """Abstract base trigger interface."""

    @abstractmethod
    async def evaluate(self, payload: dict[str, Any], context: dict[str, Any]) -> bool:
        """Evaluates whether trigger conditions are met to fire workflow execution."""
        pass


class ManualTrigger(Trigger):
    """Fires workflow upon direct user initiation."""

    async def evaluate(self, payload: dict[str, Any], context: dict[str, Any]) -> bool:
        return True


class EventTrigger(Trigger):
    """Fires workflow when a system event (e.g. database change, file upload) occurs."""

    def __init__(self, event_name: str | None = None):
        self.event_name = event_name

    async def evaluate(self, payload: dict[str, Any], context: dict[str, Any]) -> bool:
        if not self.event_name:
            return True
        incoming_event = payload.get("event") or context.get("event")
        return incoming_event == self.event_name


class ScheduleTrigger(Trigger):
    """Fires workflow according to cron or periodic schedule specification."""

    def __init__(self, cron_expression: str = "* * * * *"):
        self.cron_expression = cron_expression

    async def evaluate(self, payload: dict[str, Any], context: dict[str, Any]) -> bool:
        # Evaluated by scheduler worker
        return True
