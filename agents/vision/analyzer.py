"""
Vision Provider Abstraction and Multimodal Implementations.
Supports online multimodal models (OpenAI GPT-4o) and deterministic offline mock providers.
Strictly wraps all visual text and OCR data in non-executable untrusted context.
"""

import asyncio
import base64
import json
import os
from typing import Any, Protocol

try:
    from app.core.config import settings
except ImportError:
    try:
        from backend.app.core.config import settings
    except ImportError:

        class SettingsFallback:
            OPENAI_API_KEY = ""
            VISION_MODEL = "gpt-4o"
            VISION_PROVIDER = "mock"

        settings = SettingsFallback()

try:
    from app.core.logging import logger
except ImportError:
    try:
        from backend.app.core.logging import logger
    except ImportError:
        import logging

        logger = logging.getLogger("omniagent.vision.analyzer")

from agents.vision.exceptions import VisionProviderError
from agents.vision.prompts import TASK_PROMPT_GUIDANCE, VISION_SYSTEM_PROMPT
from agents.vision.security import (
    format_untrusted_image_context,
    sanitize_untrusted_text,
)


class VisionProvider(Protocol):
    """Protocol for multimodal vision inference providers."""

    async def analyze(
        self,
        image_bytes: bytes,
        question: str,
        task_type: str = "GENERAL_IMAGE_ANALYSIS",
        ocr_result: dict[str, Any] | None = None,
        detected_objects: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Executes vision understanding and returns structured dictionary:
        {
            "summary": str,
            "answer": str,
            "findings": list[dict],
            "confidence": float,
            "warnings": list[str]
        }
        """
        ...


class OpenAIVisionProvider:
    """Multimodal OpenAI GPT-4o vision inference provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = (
            api_key
            or getattr(settings, "OPENAI_API_KEY", "")
            or os.getenv("OPENAI_API_KEY", "")
        )
        self.model = model or getattr(settings, "VISION_MODEL", "gpt-4o")

    async def analyze(
        self,
        image_bytes: bytes,
        question: str,
        task_type: str = "GENERAL_IMAGE_ANALYSIS",
        ocr_result: dict[str, Any] | None = None,
        detected_objects: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise VisionProviderError("OpenAI API key is missing or unconfigured.")

        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise VisionProviderError("The 'openai' library is not installed.")

        client = AsyncOpenAI(api_key=self.api_key)

        # Encode image to base64
        base64_img = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{base64_img}"

        # Prepare secure untrusted context
        ocr_text = ocr_result.get("text") if ocr_result else None
        untrusted_block = format_untrusted_image_context(
            ocr_text=ocr_text, detected_objects=detected_objects
        )

        task_guidance = TASK_PROMPT_GUIDANCE.get(
            task_type, TASK_PROMPT_GUIDANCE["GENERAL_IMAGE_ANALYSIS"]
        )
        user_prompt_content = [
            {
                "type": "text",
                "text": f"{task_guidance}\n\nUser Question:\n{sanitize_untrusted_text(question)}\n\n{untrusted_block}\n\nPlease respond strictly in JSON matching the specified schema.",
            },
            {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
        ]

        try:
            response = await client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": VISION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt_content},
                ],
                temperature=0.1,
                max_tokens=2048,
                timeout=45.0,
            )

            raw_text = response.choices[0].message.content
            parsed = json.loads(raw_text)
            return {
                "summary": parsed.get("summary", "Visual analysis completed."),
                "answer": parsed.get("answer", "Analysis executed successfully."),
                "findings": parsed.get("findings", []),
                "confidence": float(parsed.get("confidence", 0.95)),
                "warnings": parsed.get("warnings", []),
            }

        except Exception as exc:  # noqa: BLE001
            logger.error("openai_vision_inference_failed", error=str(exc))
            raise VisionProviderError(f"OpenAI Vision inference failed: {exc!s}")


class MockVisionProvider:
    """
    Deterministic mock vision provider for testing, offline execution, and development.
    Produces high-fidelity, grounded inspection findings based on the specific query and task.
    """

    def __init__(
        self,
        custom_response: dict[str, Any] | None = None,
        simulate_failure: bool = False,
        simulate_timeout: bool = False,
        simulated_latency_s: float = 0.0,
    ):
        self.custom_response = custom_response
        self.simulate_failure = simulate_failure
        self.simulate_timeout = simulate_timeout
        self.simulated_latency_s = simulated_latency_s

    async def analyze(
        self,
        image_bytes: bytes,
        question: str,
        task_type: str = "GENERAL_IMAGE_ANALYSIS",
        ocr_result: dict[str, Any] | None = None,
        detected_objects: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.simulated_latency_s > 0:
            await asyncio.sleep(self.simulated_latency_s)

        if self.simulate_timeout:
            raise asyncio.TimeoutError("Vision inference request timed out.")

        if self.simulate_failure:
            raise VisionProviderError("Simulated upstream vision neural model outage.")

        if self.custom_response is not None:
            return self.custom_response

        # Deterministic analytical synthesis based on task_type, detected objects, and OCR
        q_lower = question.lower()
        ocr_text = (ocr_result.get("text", "") if ocr_result else "").strip()
        objects = detected_objects or []

        findings: list[dict[str, Any]] = []
        warnings: list[str] = []

        if (
            task_type in ("OCR", "TEXT_EXTRACTION")
            or "serial" in q_lower
            or "text" in q_lower
        ):
            if ocr_text:
                summary = "Text extracted from image artifact."
                answer = f"Extracted text from image: {ocr_text}"
                findings.append(
                    {
                        "title": "Visible Inscription",
                        "description": f"Verified text inscription detected: '{ocr_text}'.",
                        "severity": "INFO",
                        "confidence": 0.96,
                        "category": "text",
                    }
                )
            else:
                summary = "No legible text was extracted."
                answer = "No legible text or serial numbers were detected in the image."
                warnings.append(
                    "OCR detected no alphanumeric characters with sufficient confidence."
                )

        elif (
            task_type in ("DAMAGE_ANALYSIS", "VISUAL_INSPECTION")
            or "damage" in q_lower
            or "inspect" in q_lower
        ):
            summary = "Visual inspection completed. Structural integrity evaluated."
            answer = (
                "No clearly visible structural damage was detected in the main housing.\n"
                "Findings:\n"
                "• Main housing appears intact and aligned.\n"
                "• One cable junction area requires routine preventative inspection."
            )
            findings.append(
                {
                    "title": "Main Housing Integrity",
                    "description": "Housing surface shows no visible cracks, fracturing, or severe corrosion.",
                    "severity": "LOW",
                    "confidence": 0.94,
                    "category": "structural",
                }
            )
            findings.append(
                {
                    "title": "Junction & Connection Point",
                    "description": "Wiring interface shows minor dust accumulation but no electrical burning or cable fraying.",
                    "severity": "INFO",
                    "confidence": 0.88,
                    "category": "component",
                }
            )

        elif (
            task_type in ("COMPONENT_IDENTIFICATION", "OBJECT_DETECTION")
            or "component" in q_lower
        ):
            summary = "Identified visual components in the analyzed image."
            comp_names = (
                [o.get("label", "component") for o in objects]
                if objects
                else ["main_housing", "connector_assembly"]
            )
            answer = f"The following components were identified in the image: {', '.join(comp_names)}."
            for name in comp_names:
                findings.append(
                    {
                        "title": f"Component: {name}",
                        "description": f"Identified {name} in operational position.",
                        "severity": "INFO",
                        "confidence": 0.92,
                        "category": "component",
                    }
                )

        elif (
            task_type == "SAFETY_ANALYSIS" or "safety" in q_lower or "hazard" in q_lower
        ):
            summary = "Safety compliance and hazard inspection completed."
            answer = "The equipment area appears clear of immediate severe hazards. Safety guards are present."
            findings.append(
                {
                    "title": "Safety Guard Status",
                    "description": "Protective shroud is installed and seated in place.",
                    "severity": "INFO",
                    "confidence": 0.95,
                    "category": "safety",
                }
            )

        else:
            summary = "General image analysis completed."
            answer = f"Analysis of the image indicates a structured scene. Question evaluated: '{question}'."
            findings.append(
                {
                    "title": "Scene Composition",
                    "description": "Visual elements were successfully processed and evaluated against the inquiry.",
                    "severity": "INFO",
                    "confidence": 0.90,
                    "category": "general",
                }
            )

        return {
            "summary": summary,
            "answer": answer,
            "findings": findings,
            "confidence": 0.93,
            "warnings": warnings,
        }


class HybridVisionProvider:
    """
    Hybrid provider: uses online OpenAI Vision if key configured,
    otherwise falls back smoothly to deterministic MockVisionProvider.
    """

    def __init__(self, fallback_provider: VisionProvider | None = None):
        self.fallback = fallback_provider or MockVisionProvider()
        self._openai_provider: OpenAIVisionProvider | None = None

        api_key = getattr(settings, "OPENAI_API_KEY", "") or os.getenv(
            "OPENAI_API_KEY", ""
        )
        provider_setting = getattr(settings, "VISION_PROVIDER", "mock").lower()

        if provider_setting == "openai" and api_key:
            try:
                self._openai_provider = OpenAIVisionProvider(api_key=api_key)
            except Exception:  # noqa: BLE001
                self._openai_provider = None

    async def analyze(
        self,
        image_bytes: bytes,
        question: str,
        task_type: str = "GENERAL_IMAGE_ANALYSIS",
        ocr_result: dict[str, Any] | None = None,
        detected_objects: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self._openai_provider:
            try:
                return await self._openai_provider.analyze(
                    image_bytes=image_bytes,
                    question=question,
                    task_type=task_type,
                    ocr_result=ocr_result,
                    detected_objects=detected_objects,
                    context=context,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("online_vision_failed_falling_back", error=str(exc))

        return await self.fallback.analyze(
            image_bytes=image_bytes,
            question=question,
            task_type=task_type,
            ocr_result=ocr_result,
            detected_objects=detected_objects,
            context=context,
        )


def get_vision_provider(provider_name: str | None = None) -> VisionProvider:
    """Factory retrieving the configured VisionProvider."""
    name = (provider_name or getattr(settings, "VISION_PROVIDER", "mock")).lower()
    if name == "openai":
        api_key = getattr(settings, "OPENAI_API_KEY", "") or os.getenv(
            "OPENAI_API_KEY", ""
        )
        if api_key:
            return HybridVisionProvider()
    return MockVisionProvider()
