import json
import os
from abc import ABC, abstractmethod
from typing import Any

from app.agents.document.exceptions import DocumentLLMError
from app.agents.document.router import (
    extract_deterministic_invoice,
    extract_deterministic_policy,
    extract_deterministic_report,
    extract_deterministic_technical_manual,
    heuristic_classify_document,
)
from app.agents.document.schemas import DocumentPage, DocumentType

try:
    from app.core.config import settings
except ImportError:
    try:
        from backend.app.core.config import settings
    except ImportError:
        settings = None


class BaseDocumentLLMProvider(ABC):
    """Abstract interface for Document Agent LLM inference and structured JSON extraction."""

    @abstractmethod
    async def generate_understanding_json(
        self,
        document_text: str,
        pages: list[DocumentPage],
        task: str,
        query: str | None = None,
        system_prompt: str | None = None
    ) -> dict[str, Any]:
        """
        Executes document understanding inference and returns a dictionary matching DocumentAnalysisResult.
        Must raise DocumentLLMError on critical provider failure or malformed payload.
        """


class DeterministicDocumentProvider(BaseDocumentLLMProvider):
    """
    High-precision deterministic rule-based document analyzer.
    Extracts structured domain schemas based on regex, keywords, and structural patterns.
    """

    async def generate_understanding_json(
        self,
        document_text: str,
        pages: list[DocumentPage],
        task: str,
        query: str | None = None,
        system_prompt: str | None = None
    ) -> dict[str, Any]:
        doc_type, confidence, title = heuristic_classify_document(document_text)

        key_points = []
        summary = ""
        structured_data = {}
        sources = []

        if doc_type == DocumentType.INVOICE:
            inv_data, inv_sources = extract_deterministic_invoice(document_text, pages)
            structured_data = inv_data.model_dump()
            sources = inv_sources
            summary = (
                f"Invoice from vendor '{inv_data.vendor}' for total amount of {inv_data.total} {inv_data.currency}."
                if inv_data.total != "Not found in the provided document."
                else "Invoice billing document."
            )
            key_points = [
                f"Vendor: {inv_data.vendor}",
                f"Invoice #: {inv_data.invoice_number}",
                f"Date: {inv_data.date}",
                f"Total Amount: {inv_data.total} {inv_data.currency}",
                f"Line Items Count: {len(inv_data.line_items)}"
            ]

        elif doc_type == DocumentType.POLICY:
            pol_data, pol_sources = extract_deterministic_policy(document_text, pages)
            structured_data = pol_data.model_dump()
            sources = pol_sources
            summary = pol_data.summary or "Company policy document."
            key_points = pol_data.important_rules[:5]

        elif doc_type == DocumentType.TECHNICAL_MANUAL:
            man_data, man_sources = extract_deterministic_technical_manual(document_text, pages)
            structured_data = man_data.model_dump()
            sources = man_sources
            summary = man_data.summary or "Technical manual and operating specifications."
            key_points = (man_data.key_instructions[:3] + man_data.warnings[:2])

        elif doc_type == DocumentType.REPORT:
            rep_data, rep_sources = extract_deterministic_report(document_text, pages)
            structured_data = rep_data.model_dump()
            sources = rep_sources
            summary = rep_data.executive_summary or "Executive report summary."
            key_points = rep_data.important_findings[:5]

        else:
            first_lines = [line.strip() for line in document_text.split("\n") if line.strip()]
            summary = first_lines[0] if first_lines else "Enterprise document."
            key_points = first_lines[1:6] if len(first_lines) > 1 else ["Content verified."]
            structured_data = {"text_preview": summary}

        return {
            "document_type": doc_type.value,
            "title": title,
            "summary": summary,
            "key_points": key_points,
            "entities": {
                "organization": "OmniAgent Enterprise",
                "detected_type": doc_type.value
            },
            "structured_data": structured_data,
            "sources": sources,
            "confidence": confidence,
            "warnings": []
        }


class OpenAIDocumentLLMProvider(BaseDocumentLLMProvider):
    """Production OpenAI document understanding provider using JSON mode."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o"):
        self.api_key = api_key or (getattr(settings, "OPENAI_API_KEY", "") if settings else "") or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self._client = None

    def _get_client(self):
        if not self.api_key:
            raise DocumentLLMError("OPENAI_API_KEY is not configured for document understanding.")
        if not self._client:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def generate_understanding_json(
        self,
        document_text: str,
        pages: list[DocumentPage],
        task: str,
        query: str | None = None,
        system_prompt: str | None = None
    ) -> dict[str, Any]:
        client = self._get_client()
        prompt = (
            f"Analyze the following document and output valid JSON with keys: "
            f"document_type, title, summary, key_points, entities, structured_data, sources, confidence.\n\n"
            f"Task: {task}\nQuery: {query or 'None'}\n\nDocument Text:\n{document_text[:8000]}"
        )
        try:
            response = await client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt or "You are an enterprise document intelligence agent."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception as exc:
            raise DocumentLLMError(f"OpenAI document extraction failed: {exc!s}") from exc


class HybridDocumentLLMProvider(BaseDocumentLLMProvider):
    """
    Hybrid provider: evaluates deterministic heuristics first, falling back to OpenAI when needed.
    """

    def __init__(self):
        self.deterministic_provider = DeterministicDocumentProvider()
        api_key = (getattr(settings, "OPENAI_API_KEY", "") if settings else "") or os.getenv("OPENAI_API_KEY", "")
        self.openai_provider = OpenAIDocumentLLMProvider(api_key=api_key) if api_key else None

    async def generate_understanding_json(
        self,
        document_text: str,
        pages: list[DocumentPage],
        task: str,
        query: str | None = None,
        system_prompt: str | None = None
    ) -> dict[str, Any]:
        result = await self.deterministic_provider.generate_understanding_json(
            document_text=document_text,
            pages=pages,
            task=task,
            query=query,
            system_prompt=system_prompt
        )
        # If deterministic confidence is high or OpenAI is not configured, return deterministic result
        if result.get("confidence", 0) >= 0.85 or not self.openai_provider:
            return result

        try:
            return await self.openai_provider.generate_understanding_json(
                document_text=document_text,
                pages=pages,
                task=task,
                query=query,
                system_prompt=system_prompt
            )
        except DocumentLLMError:
            return result


def get_default_document_llm_provider() -> BaseDocumentLLMProvider:
    """Returns the default production hybrid document LLM provider."""
    return HybridDocumentLLMProvider()
