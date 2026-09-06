import asyncio
from abc import ABC, abstractmethod
from typing import Any

from agents.supervisor.exceptions import LLMProviderError
from agents.supervisor.router import deterministic_classify


class BaseLLMProvider(ABC):
    """Abstract interface for LLM classification and structured extraction."""

    @abstractmethod
    async def generate_decision_json(
        self,
        user_message: str,
        system_prompt: str,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Executes inference and returns a dictionary matching SupervisorDecision schema.
        Must raise LLMProviderError on critical provider failure or malformed payload.
        """


class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM provider for deterministic, offline testing and fault-injection simulations.
    Supports injecting latency, timeouts, malformed outputs, and custom decision responses.
    """

    def __init__(
        self,
        custom_response: dict[str, Any] | None = None,
        simulate_timeout: bool = False,
        simulate_malformed: bool = False,
        simulate_error: bool = False,
        simulated_latency_s: float = 0.0,
    ):
        self.custom_response = custom_response
        self.simulate_timeout = simulate_timeout
        self.simulate_malformed = simulate_malformed
        self.simulate_error = simulate_error
        self.simulated_latency_s = simulated_latency_s

    async def generate_decision_json(
        self,
        user_message: str,
        system_prompt: str,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if self.simulated_latency_s > 0:
            await asyncio.sleep(self.simulated_latency_s)

        if self.simulate_timeout:
            raise asyncio.TimeoutError("LLM inference timed out after timeout threshold.")

        if self.simulate_error:
            raise LLMProviderError("Simulated upstream LLM service outage.")

        if self.simulate_malformed:
            return {"corrupt": True, "syntax_error": None}

        if self.custom_response:
            return self.custom_response

        # Fallback to deterministic classifier output formatted as dict
        decision = deterministic_classify(user_message)
        if decision:
            return decision.model_dump()

        return {
            "intent": "general_query",
            "task_type": "GENERAL_QUERY",
            "capability": "general_assistance",
            "selected_agent": "supervisor",
            "priority": "medium",
            "confidence": 0.85,
            "requires_tool": False,
            "requires_approval": False,
            "task_plan": ["Review user question", "Synthesize direct response"],
            "explanation": "General enterprise inquiry resolved by Supervisor."
        }


class HybridDeterministicProvider(BaseLLMProvider):
    """
    High-efficiency provider that evaluates deterministic rules first.
    If no rule matches, it falls back to an online provider or safe classification.
    """

    def __init__(self, fallback_provider: BaseLLMProvider | None = None):
        self.fallback_provider = fallback_provider or MockLLMProvider()

    async def generate_decision_json(
        self,
        user_message: str,
        system_prompt: str,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        # Fast path: instant deterministic evaluation
        decision = deterministic_classify(user_message)
        if decision:
            return decision.model_dump()

        # Fallback to secondary provider
        return await self.fallback_provider.generate_decision_json(
            user_message=user_message,
            system_prompt=system_prompt,
            context=context
        )


def get_default_llm_provider() -> BaseLLMProvider:
    """Returns the production-ready hybrid provider with deterministic fast-path."""
    return HybridDeterministicProvider()
