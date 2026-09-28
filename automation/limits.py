"""
OmniAgent AI — Automation Workflow Execution Limits
"""

from app.core.config import settings

WORKFLOW_MAX_STEPS = getattr(settings, "WORKFLOW_MAX_STEPS", 30)
WORKFLOW_MAX_EXECUTION_SECONDS = float(getattr(settings, "WORKFLOW_MAX_EXECUTION_SECONDS", 300))
APPROVAL_EXPIRATION_MINUTES = getattr(settings, "APPROVAL_EXPIRATION_MINUTES", 30)
