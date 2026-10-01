import os
from abc import ABC, abstractmethod

from app.agents.rag.exceptions import RAGGenerationError
from app.agents.rag.prompts import (
    RAG_FALLBACK_ANSWER,
    RAG_SYSTEM_PROMPT,
    RAG_USER_PROMPT_TEMPLATE,
)

try:
    from app.core.config import settings
except ImportError:
    try:
        from backend.app.core.config import settings
    except ImportError:
        settings = None


class BaseRAGLLMProvider(ABC):
    """Abstract interface for RAG LLM inference and grounded answer synthesis."""

    @abstractmethod
    async def generate_rag_answer(
        self,
        question: str,
        context: str,
        system_prompt: str | None = None
    ) -> tuple[str, bool, float]:
        """
        Executes grounded generation using the provided context.
        Returns: (answer_text, is_grounded, confidence_score)
        """


class OpenAIRAGLLMProvider(BaseRAGLLMProvider):
    """
    Production OpenAI LLM provider using gpt-4o with strict temperature=0.0.
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o"):
        self.api_key = api_key or (getattr(settings, "OPENAI_API_KEY", "") if settings else "") or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self._client = None

    def _get_client(self):
        if not self.api_key:
            raise RAGGenerationError(
                "OPENAI_API_KEY is not configured. RAG answer synthesis requires a valid OpenAI API key."
            )
        if not self._client:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise RAGGenerationError("The 'openai' package is required for OpenAIRAGLLMProvider.")
        return self._client

    async def generate_rag_answer(
        self,
        question: str,
        context: str,
        system_prompt: str | None = None
    ) -> tuple[str, bool, float]:
        if not self.api_key:
            raise RAGGenerationError(
                "OPENAI_API_KEY is not configured. RAG answer synthesis requires a valid OpenAI API key."
            )

        sys_prompt = system_prompt or RAG_SYSTEM_PROMPT
        user_prompt = RAG_USER_PROMPT_TEMPLATE.format(context=context, question=question)

        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self.model,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            raw_answer = response.choices[0].message.content.strip()

            if RAG_FALLBACK_ANSWER.lower() in raw_answer.lower():
                return RAG_FALLBACK_ANSWER, False, 0.0

            return raw_answer, True, 0.92

        except Exception as exc:
            raise RAGGenerationError(f"OpenAI LLM completion failed: {exc!s}") from exc


def get_default_rag_llm_provider() -> BaseRAGLLMProvider:
    """Returns the default configured RAG LLM provider."""
    api_key = (getattr(settings, "OPENAI_API_KEY", "") if settings else "") or os.getenv("OPENAI_API_KEY", "")
    model = getattr(settings, "DEFAULT_MODEL", "gpt-4o") if settings else "gpt-4o"
    if not api_key:
        raise RAGGenerationError(
            "OPENAI_API_KEY is not configured. RAG answer synthesis requires a valid OpenAI API key."
        )
    return OpenAIRAGLLMProvider(api_key=api_key, model=model)
