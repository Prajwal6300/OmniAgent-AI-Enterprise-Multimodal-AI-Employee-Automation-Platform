"""
OmniAgent AI — Orchestration Routing Logic
Conditional edge functions directing graph control flow between evaluation,
reasoning synthesis, action requests, approval pauses, verification, and finalization.
"""

from typing import Literal
from app.orchestration.state import OrchestrationState


def route_after_supervisor(state: OrchestrationState) -> Literal["route_request", "finalize"]:
    """Routes from supervisor to target agent dispatch or direct finalization."""
    target = state.get("target_agent", "supervisor")
    if target in ("supervisor", "finalize", "end"):
        return "finalize"
    return "route_request"


def route_after_evaluate(state: OrchestrationState) -> Literal["finalize", "reasoning", "action", "route_request"]:
    """Routes following specialist evaluation."""
    next_step = state.get("next_step")
    if next_step == "action":
        return "action"
    if next_step == "reasoning":
        return "reasoning"
    if next_step == "route_agent":
        return "route_request"
    return "finalize"


def route_after_reasoning(state: OrchestrationState) -> Literal["action", "finalize"]:
    """Routes from reasoning either to action or straight to finalization."""
    if state.get("action_requested"):
        return "action"
    return "finalize"


def route_after_approval_check(state: OrchestrationState) -> Literal["pause", "verify"]:
    """Pauses graph if approval is required and ungranted; otherwise proceeds to verification."""
    if state.get("status") == "WAITING_FOR_APPROVAL" or state.get("pending_approval"):
        return "pause"
    return "verify"
