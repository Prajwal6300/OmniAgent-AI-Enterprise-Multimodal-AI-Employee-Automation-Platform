import asyncio
import os
import re
from abc import ABC, abstractmethod
from typing import Any

from agents.rag.exceptions import RAGGenerationError
from agents.rag.prompts import RAG_FALLBACK_ANSWER, RAG_SYSTEM_PROMPT, RAG_USER_PROMPT_TEMPLATE

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
        pass


class MockRAGLLMProvider(BaseRAGLLMProvider):
    """
    Production-grade mock provider for deterministic offline execution, unit tests,
    and anti-hallucination validation.
    """

    def __init__(
        self,
        custom_answer: str | None = None,
        custom_grounded: bool | None = None,
        custom_confidence: float | None = None,
        simulate_timeout: bool = False,
        simulate_error: bool = False,
        simulated_latency_s: float = 0.0,
    ):
        self.custom_answer = custom_answer
        self.custom_grounded = custom_grounded
        self.custom_confidence = custom_confidence
        self.simulate_timeout = simulate_timeout
        self.simulate_error = simulate_error
        self.simulated_latency_s = simulated_latency_s

    async def generate_rag_answer(
        self,
        question: str,
        context: str,
        system_prompt: str | None = None
    ) -> tuple[str, bool, float]:
        if self.simulated_latency_s > 0:
            await asyncio.sleep(self.simulated_latency_s)

        if self.simulate_timeout:
            raise TimeoutError("Simulated LLM generation timeout.")

        if self.simulate_error:
            raise RAGGenerationError("Simulated LLM internal generation error.")

        if self.custom_answer is not None:
            grounded = self.custom_grounded if self.custom_grounded is not None else True
            conf = self.custom_confidence if self.custom_confidence is not None else 1.0
            return self.custom_answer, grounded, conf

        # Deterministic Grounded Synthesizer
        # 1. If context is empty, refuse to answer
        if not context or not context.strip():
            return RAG_FALLBACK_ANSWER, False, 0.0

        q_lower = question.lower()
        ctx_lower = context.lower()

        # 2. Extract key terms from question (ignoring stop words)
        stop_words = {"what", "is", "the", "company's", "company", "our", "for", "this", "to", "in", "of", "and", "a", "an", "how", "does", "are", "do", "we"}
        category_words = {"policy", "leave", "agreement", "manual", "procedure", "rules", "guidelines", "instructions", "terms", "term", "standard", "standards"}
        tokens = [w for w in re.findall(r"\w+", q_lower) if w not in stop_words and len(w) > 2]

        qualifiers = [t for t in tokens if t not in category_words]

        # If specific qualifiers were requested (e.g. "maternity") but absent from context, refuse
        if qualifiers and not any(t in ctx_lower for t in qualifiers):
            return RAG_FALLBACK_ANSWER, False, 0.0

        # Check if question tokens appear in context
        matching_tokens = [t for t in tokens if t in ctx_lower]

        # If question has key terms but none match the context, safely refuse
        if tokens and not matching_tokens:
            return RAG_FALLBACK_ANSWER, False, 0.0

        # 3. Extract relevant sentence or passage from context
        passages = [p.strip() for p in context.split("\n\n---\n\n") if p.strip()]
        matched_passage = None
        for p in passages:
            p_lower = p.lower()
            if any(t in p_lower for t in matching_tokens):
                matched_passage = p
                break

        if not matched_passage and passages:
            matched_passage = passages[0]

        if not matched_passage:
            return RAG_FALLBACK_ANSWER, False, 0.0

        # Extract source header if present: [Source: Foo.pdf | Page 3]
        source_tag = ""
        header_match = re.search(r"^\[(.*?)\]", matched_passage)
        if header_match:
            header_text = header_match.group(1)
            # Reformat to [Source: <Name>, Page <Num>]
            parts = [pt.strip() for pt in header_text.split("|")]
            doc_part = next((pt.replace("Source:", "").strip() for pt in parts if pt.startswith("Source:")), "Document")
            page_part = next((pt for pt in parts if pt.startswith("Page")), None)
            if page_part:
                source_tag = f" [Source: {doc_part}, {page_part}]"
            else:
                source_tag = f" [Source: {doc_part}]"

        # Clean body text (remove source header)
        body_text = re.sub(r"^\[.*?\]\n?", "", matched_passage).strip()
        first_sentence = body_text.split(". ")[0].strip()
        if not first_sentence.endswith("."):
            first_sentence += "."

        # Synthesize grounded answer
        answer = f"{first_sentence}{source_tag}"
        return answer, True, 0.95


class OpenAIRAGLLMProvider(BaseRAGLLMProvider):
    """
    Production OpenAI LLM provider using gpt-4o with strict temperature=0.0.
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self._client = None

    def _get_client(self):
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
            # Fallback to deterministic mock provider if API key not supplied
            fallback = MockRAGLLMProvider()
            return await fallback.generate_rag_answer(question, context, system_prompt)

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
    api_key = os.getenv("OPENAI_API_KEY", getattr(settings, "OPENAI_API_KEY", "") if settings else "")
    model = getattr(settings, "DEFAULT_MODEL", "gpt-4o") if settings else "gpt-4o"
    if api_key:
        return OpenAIRAGLLMProvider(api_key=api_key, model=model)
    return MockRAGLLMProvider()
