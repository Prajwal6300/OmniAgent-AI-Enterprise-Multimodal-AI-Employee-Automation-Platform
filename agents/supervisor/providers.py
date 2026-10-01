import json
import os
from abc import ABC, abstractmethod
from typing import Any

from agents.supervisor.exceptions import LLMProviderError
from agents.supervisor.router import deterministic_classify

try:
    from app.core.config import settings
except ImportError:
    try:
        from backend.app.core.config import settings
    except ImportError:
        settings = None


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


class DeterministicSupervisorProvider(BaseLLMProvider):
    """Deterministic fast-path provider evaluating rule-based intent classifiers."""

    async def generate_decision_json(
        self,
        user_message: str,
        system_prompt: str,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
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


class OpenAISupervisorProvider(BaseLLMProvider):
    """Production OpenAI LLM provider using structured JSON routing."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o"):
        self.api_key = api_key or (getattr(settings, "OPENAI_API_KEY", "") if settings else "") or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self._client = None

    def _get_client(self):
        if not self.api_key:
            raise LLMProviderError("OPENAI_API_KEY is not configured for supervisor routing.")
        if not self._client:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def generate_decision_json(
        self,
        user_message: str,
        system_prompt: str,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        client = self._get_client()
        try:
            response = await client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Classify and route the following request:\n{user_message}"}
                ],
                temperature=0.0
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception as exc:
            raise LLMProviderError(f"OpenAI supervisor routing failed: {exc!s}") from exc


class HybridDeterministicProvider(BaseLLMProvider):
    """
    High-efficiency provider that evaluates deterministic rules first.
    If no rule matches, it falls back to OpenAI or safe deterministic default.
    """

    def __init__(self, fallback_provider: BaseLLMProvider | None = None):
        self.fallback_provider = fallback_provider or DeterministicSupervisorProvider()
        api_key = (getattr(settings, "OPENAI_API_KEY", "") if settings else "") or os.getenv("OPENAI_API_KEY", "")
        self.openai_provider = OpenAISupervisorProvider(api_key=api_key) if api_key else None

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

        if self.openai_provider:
            try:
                return await self.openai_provider.generate_decision_json(
                    user_message=user_message,
                    system_prompt=system_prompt,
                    context=context
                )
            except LLMProviderError:
                pass

        return await self.fallback_provider.generate_decision_json(
            user_message=user_message,
            system_prompt=system_prompt,
            context=context
        )


def get_default_llm_provider() -> BaseLLMProvider:
    """Returns the production-ready hybrid provider with deterministic fast-path."""
    return HybridDeterministicProvider()
