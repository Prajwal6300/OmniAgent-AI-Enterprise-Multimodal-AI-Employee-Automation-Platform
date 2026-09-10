import asyncio
from abc import ABC, abstractmethod
from typing import Any

from agents.document.exceptions import DocumentLLMError
from agents.document.router import (
    extract_deterministic_invoice,
    extract_deterministic_policy,
    extract_deterministic_report,
    extract_deterministic_technical_manual,
    heuristic_classify_document,
)
from agents.document.schemas import DocumentPage, DocumentType


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


class MockDocumentLLMProvider(BaseDocumentLLMProvider):
    """
    Mock LLM provider for deterministic offline execution, unit tests, and fault injection.
    Supports injecting latency, timeouts, malformed payloads, and custom structured responses.
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

    async def generate_understanding_json(
        self,
        document_text: str,
        pages: list[DocumentPage],
        task: str,
        query: str | None = None,
        system_prompt: str | None = None
    ) -> dict[str, Any]:
        if self.simulated_latency_s > 0:
            await asyncio.sleep(self.simulated_latency_s)

        if self.simulate_timeout:
            raise asyncio.TimeoutError("Document LLM inference timed out.")

        if self.simulate_error:
            raise DocumentLLMError("Simulated upstream LLM service outage.")

        if self.simulate_malformed:
            return {"syntax_error": "corrupted", "invalid_json": True}

        if self.custom_response:
            return self.custom_response

        # High-precision deterministic fallback synthesizer
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
            first_lines = [l.strip() for l in document_text.split("\n") if l.strip()]
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


class HybridDocumentLLMProvider(BaseDocumentLLMProvider):
    """
    Hybrid provider leveraging deterministic heuristics for speed, with fallback to secondary provider.
    """

    def __init__(self, fallback_provider: BaseDocumentLLMProvider | None = None):
        self.fallback_provider = fallback_provider or MockDocumentLLMProvider()

    async def generate_understanding_json(
        self,
        document_text: str,
        pages: list[DocumentPage],
        task: str,
        query: str | None = None,
        system_prompt: str | None = None
    ) -> dict[str, Any]:
        return await self.fallback_provider.generate_understanding_json(
            document_text=document_text,
            pages=pages,
            task=task,
            query=query,
            system_prompt=system_prompt
        )


def get_default_document_llm_provider() -> BaseDocumentLLMProvider:
    """Returns the default deterministic/hybrid document LLM provider."""
    return HybridDocumentLLMProvider()
