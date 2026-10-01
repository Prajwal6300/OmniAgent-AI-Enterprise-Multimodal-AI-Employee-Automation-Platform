"""
OmniAgent AI — Celery Application Configuration
Configures Celery worker and Celery Beat scheduler with task_acks_late=True,
prefetch limits, and automated SLA / watchdog intervals.
"""

from typing import Any

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

try:
    from celery import Celery

    celery_app = Celery(
        "omniagent",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    celery_app.conf.update(
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_default_retry_delay=60,
        task_max_retries=3,
        beat_schedule={
            "approval-sla-escalation-every-30-min": {
                "task": "app.workers.tasks.escalate_pending_approvals",
                "schedule": 1800.0,
            },
            "hung-workflow-watchdog-every-15-min": {
                "task": "app.workers.tasks.watchdog_hung_workflow_runs",
                "schedule": 900.0,
            },
        },
    )
    HAS_CELERY = True
except ImportError:
    HAS_CELERY = False

    class FallbackCelery:
        """Lightweight task decorator for local development and test suites."""

        def task(self, *dargs: Any, **dkwargs: Any):
            def decorator(fn):
                def delay(*args, **kwargs):
                    return fn(*args, **kwargs)

                fn.delay = delay
                return fn

            return decorator

    celery_app = FallbackCelery()
