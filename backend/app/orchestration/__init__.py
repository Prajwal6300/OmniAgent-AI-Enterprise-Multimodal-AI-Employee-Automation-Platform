"""
OmniAgent AI — Central Orchestration Layer
Unified cognitive orchestrator connecting Supervisor, Document, RAG, Database,
Vision, Reasoning, and Action agents with human-in-the-loop governance.
"""

from app.orchestration.errors import (
    ActionExecutionFailedError,
    ExecutionTimeoutError,
    InvalidApprovalError,
    MaxAgentCallsExceededError,
    MaxStepsExceededError,
    OrchestrationError,
    PromptInjectionDetectedError,
    RequestCancelledError,
    TenantSecurityViolationError,
    UnauthorizedAgentCallError,
    UnsafeTransitionError,
)
from app.orchestration.events import (
    EventRecorder,
    OrchestrationEvent,
    OrchestrationEventType,
    event_recorder,
)
from app.orchestration.executor import (
    OrchestrationAgentExecutor,
    detect_evidence_conflicts,
    executor,
)
from app.orchestration.graph import (
    Orchestrator,
    build_orchestration_graph,
    run_linear_orchestration,
)
from app.orchestration.limits import (
    OrchestrationLimits,
    enforce_agent_call_limit,
    enforce_execution_timeout,
    enforce_step_limit,
    get_orchestration_limits,
)
from app.orchestration.policies import (
    SafeTransitionPolicy,
    SecurityPolicy,
)
from app.orchestration.registry import (
    AGENT_REGISTRY,
    CANONICAL_AGENT_NAMES,
    get_agent_class,
    is_agent_registered,
    list_registered_agents,
    normalize_agent_name,
)
from app.orchestration.state import (
    ActionDetail,
    ApprovalDetail,
    AttachmentInput,
    CitationItem,
    EvidenceItem,
    ExecutionStepItem,
    OrchestrationState,
    ResumeRequest,
    UnifiedChatRequest,
    UnifiedChatResponse,
)

__all__ = [
    "AGENT_REGISTRY",
    "CANONICAL_AGENT_NAMES",
    "ActionDetail",
    "ActionExecutionFailedError",
    "ApprovalDetail",
    "AttachmentInput",
    "CitationItem",
    "EventRecorder",
    "EvidenceItem",
    "ExecutionStepItem",
    "ExecutionTimeoutError",
    "InvalidApprovalError",
    "MaxAgentCallsExceededError",
    "MaxStepsExceededError",
    "OrchestrationAgentExecutor",
    "OrchestrationError",
    "OrchestrationEvent",
    "OrchestrationEventType",
    "OrchestrationLimits",
    "OrchestrationState",
    "Orchestrator",
    "PromptInjectionDetectedError",
    "RequestCancelledError",
    "ResumeRequest",
    "SafeTransitionPolicy",
    "SecurityPolicy",
    "TenantSecurityViolationError",
    "UnauthorizedAgentCallError",
    "UnifiedChatRequest",
    "UnifiedChatResponse",
    "UnsafeTransitionError",
    "build_orchestration_graph",
    "detect_evidence_conflicts",
    "enforce_agent_call_limit",
    "enforce_execution_timeout",
    "enforce_step_limit",
    "event_recorder",
    "executor",
    "get_agent_class",
    "get_orchestration_limits",
    "is_agent_registered",
    "list_registered_agents",
    "normalize_agent_name",
    "run_linear_orchestration",
]
