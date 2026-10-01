"""
OmniAgent AI — Agent Registry
Maintains the centralized, immutable allowlist of authorized agent classes.
Rejects dynamic code loading, unknown agents, and arbitrary imports.
"""

from typing import Any

from app.agents.action.agent import ActionAgent
from app.agents.database.agent import DatabaseAgent
from app.agents.document.agent import DocumentAgent
from app.agents.rag.agent import RAGAgent
from app.agents.reasoning.agent import ReasoningAgent
from app.agents.supervisor.agent import SupervisorAgent
from app.agents.vision.agent import VisionAgent
from app.orchestration.errors import UnauthorizedAgentCallError

# Centralized, static allowlist of authorized agents
AGENT_REGISTRY: dict[str, type[Any]] = {
    "supervisor": SupervisorAgent,
    "supervisor_agent": SupervisorAgent,
    "document_agent": DocumentAgent,
    "document": DocumentAgent,
    "rag_agent": RAGAgent,
    "rag": RAGAgent,
    "database_agent": DatabaseAgent,
    "database": DatabaseAgent,
    "vision_agent": VisionAgent,
    "vision": VisionAgent,
    "reasoning_agent": ReasoningAgent,
    "reasoning": ReasoningAgent,
    "action_agent": ActionAgent,
    "action": ActionAgent,
}

# Standardized canonical names for reporting
CANONICAL_AGENT_NAMES: dict[str, str] = {
    "supervisor": "supervisor",
    "supervisor_agent": "supervisor",
    "document_agent": "document_agent",
    "document": "document_agent",
    "rag_agent": "rag_agent",
    "rag": "rag_agent",
    "database_agent": "database_agent",
    "database": "database_agent",
    "vision_agent": "vision_agent",
    "vision": "vision_agent",
    "reasoning_agent": "reasoning_agent",
    "reasoning": "reasoning_agent",
    "action_agent": "action_agent",
    "action": "action_agent",
}


def normalize_agent_name(name: str) -> str:
    """Returns canonical agent name or lowercased clean string."""
    clean = str(name).strip().lower()
    return CANONICAL_AGENT_NAMES.get(clean, clean)


def is_agent_registered(agent_name: str) -> bool:
    """Verifies whether an agent name belongs to the authorized static allowlist."""
    clean = str(agent_name).strip().lower()
    return clean in AGENT_REGISTRY


def get_agent_class(agent_name: str) -> type[Any]:
    """
    Retrieves the registered agent class.
    Raises UnauthorizedAgentCallError if the agent is unknown or unlisted.
    Never executes dynamic imports.
    """
    clean = str(agent_name).strip().lower()
    if clean not in AGENT_REGISTRY:
        raise UnauthorizedAgentCallError(
            f"Agent '{agent_name}' is not in the authorized agent allowlist. Access denied."
        )
    return AGENT_REGISTRY[clean]


def list_registered_agents() -> list[str]:
    """Returns the list of unique canonical registered agent names."""
    return sorted(set(CANONICAL_AGENT_NAMES.values()))
