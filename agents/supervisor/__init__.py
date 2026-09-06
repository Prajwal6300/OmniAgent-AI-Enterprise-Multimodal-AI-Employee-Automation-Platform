"""OmniAgent AI Supervisor Agent Package."""

from agents.supervisor.agent import SupervisorAgent
from agents.supervisor.exceptions import (
    DecisionValidationError,
    IntentClassificationError,
    LLMProviderError,
    SupervisorError,
    SupervisorValidationError,
)
from agents.supervisor.graph import build_supervisor_graph
from agents.supervisor.providers import (
    BaseLLMProvider,
    HybridDeterministicProvider,
    MockLLMProvider,
    get_default_llm_provider,
)
from agents.supervisor.router import (
    TASK_TYPE_TO_AGENT,
    TASK_TYPE_TO_CAPABILITY,
    create_fallback_decision,
    deterministic_classify,
    map_task_to_agent,
    map_task_to_capability,
)
from agents.supervisor.schemas import (
    AgentTarget,
    SupervisorAnalyzeData,
    SupervisorAnalyzeRequest,
    SupervisorDecision,
    TaskType,
)
from agents.supervisor.state import SupervisorState

__all__ = [
    "TASK_TYPE_TO_AGENT",
    "TASK_TYPE_TO_CAPABILITY",
    "AgentTarget",
    "BaseLLMProvider",
    "DecisionValidationError",
    "HybridDeterministicProvider",
    "IntentClassificationError",
    "LLMProviderError",
    "MockLLMProvider",
    "SupervisorAgent",
    "SupervisorAnalyzeData",
    "SupervisorAnalyzeRequest",
    "SupervisorDecision",
    "SupervisorError",
    "SupervisorState",
    "SupervisorValidationError",
    "TaskType",
    "build_supervisor_graph",
    "create_fallback_decision",
    "deterministic_classify",
    "get_default_llm_provider",
    "map_task_to_agent",
    "map_task_to_capability",
]
