"""
Test doubles and mock providers strictly for test execution and offline CI.
NEVER imported in production code.
"""

import asyncio
import re
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
from app.agents.rag.exceptions import RAGGenerationError
from app.agents.rag.prompts import RAG_FALLBACK_ANSWER
from app.agents.reasoning.exceptions import (
    AgentExecutionTimeoutError,
    RecursionDepthExceededError,
    TenantSecurityViolationError,
    UnsafeAgentCallError,
)
from app.agents.reasoning.executor import ALLOWED_REASONING_AGENTS, PROHIBITED_AGENTS
from app.agents.reasoning.providers import (
    classify_task_deterministically,
)
from app.agents.reasoning.schemas import Evidence, EvidenceConflict, ReasoningTaskType
from app.agents.supervisor.exceptions import LLMProviderError
from app.agents.supervisor.router import deterministic_classify
from app.agents.vision.exceptions import VisionProviderError
from app.agents.vision.schemas import ProcessorStatus


class MockRAGLLMProvider:
    """Mock RAG LLM provider for unit tests and fault-injection simulations."""

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
        system_prompt: str | None = None,
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

        if not context or not context.strip():
            return RAG_FALLBACK_ANSWER, False, 0.0

        q_lower = question.lower()
        ctx_lower = context.lower()

        stop_words = {"what", "is", "the", "company's", "company", "our", "for", "this", "to", "in", "of", "and", "a", "an", "how", "does", "are", "do", "we"}
        category_words = {"policy", "leave", "agreement", "manual", "procedure", "rules", "guidelines", "instructions", "terms", "term", "standard", "standards"}
        tokens = [w for w in re.findall(r"\w+", q_lower) if w not in stop_words and len(w) > 2]
        qualifiers = [t for t in tokens if t not in category_words]

        if qualifiers and not any(t in ctx_lower for t in qualifiers):
            return RAG_FALLBACK_ANSWER, False, 0.0

        matching_tokens = [t for t in tokens if t in ctx_lower]
        if tokens and not matching_tokens:
            return RAG_FALLBACK_ANSWER, False, 0.0

        passages = [p.strip() for p in context.split("\n\n---\n\n") if p.strip()]
        matched_passage = None
        for p in passages:
            if any(t in p.lower() for t in matching_tokens):
                matched_passage = p
                break
        if not matched_passage and passages:
            matched_passage = passages[0]
        if not matched_passage:
            return RAG_FALLBACK_ANSWER, False, 0.0

        source_tag = ""
        header_match = re.search(r"^\[(.*?)\]", matched_passage)
        if header_match:
            header_text = header_match.group(1)
            parts = [pt.strip() for pt in header_text.split("|")]
            doc_part = next((pt.replace("Source:", "").strip() for pt in parts if pt.startswith("Source:")), "Document")
            page_part = next((pt for pt in parts if pt.startswith("Page")), None)
            source_tag = f" [Source: {doc_part}, {page_part}]" if page_part else f" [Source: {doc_part}]"

        body_text = re.sub(r"^\[.*?\]\n?", "", matched_passage).strip()
        first_sentence = body_text.split(". ")[0].strip()
        if not first_sentence.endswith("."):
            first_sentence += "."

        return f"{first_sentence}{source_tag}", True, 0.95


class MockDocumentLLMProvider:
    """Mock LLM provider for offline testing of document extraction."""

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
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        if self.simulated_latency_s > 0:
            await asyncio.sleep(self.simulated_latency_s)

        if self.simulate_timeout:
            raise TimeoutError("Document LLM inference timed out.")

        if self.simulate_error:
            raise DocumentLLMError("Simulated upstream LLM service outage.")

        if self.simulate_malformed:
            return {"syntax_error": "corrupted", "invalid_json": True}

        if self.custom_response:
            return self.custom_response

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
                f"Line Items Count: {len(inv_data.line_items)}",
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
            key_points = man_data.key_instructions[:3] + man_data.warnings[:2]
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
                "detected_type": doc_type.value,
            },
            "structured_data": structured_data,
            "sources": sources,
            "confidence": confidence,
            "warnings": [],
        }


class MockReasoningLLMProvider:
    """Mock reasoning LLM provider for deterministic offline unit testing."""

    def __init__(
        self,
        custom_plan: dict[str, Any] | None = None,
        custom_synthesis: dict[str, Any] | None = None,
        simulate_timeout: bool = False,
        simulate_error: bool = False,
        simulated_latency_s: float = 0.0,
    ):
        self.custom_plan = custom_plan
        self.custom_synthesis = custom_synthesis
        self.simulate_timeout = simulate_timeout
        self.simulate_error = simulate_error
        self.simulated_latency_s = simulated_latency_s

    async def plan(
        self,
        user_question: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.simulated_latency_s > 0:
            await asyncio.sleep(self.simulated_latency_s)

        if self.simulate_timeout:
            raise TimeoutError("Reasoning planning timed out.")

        if self.simulate_error:
            raise RuntimeError("Reasoning planning LLM service outage.")

        if self.custom_plan:
            return self.custom_plan

        task_type, agents, rationale = classify_task_deterministically(user_question)
        steps = [
            {
                "agent_name": agent,
                "goal": f"Retrieve data for: {user_question}",
                "parameters": {},
            }
            for agent in agents
        ]

        return {
            "task_type": task_type,
            "agents": agents,
            "rationale": rationale,
            "steps": steps,
        }

    async def synthesize(
        self,
        user_question: str,
        task_type: str,
        evidence: list[Evidence],
        conflicts: list[EvidenceConflict],
        missing_information: list[str],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.simulated_latency_s > 0:
            await asyncio.sleep(self.simulated_latency_s)

        if self.simulate_timeout:
            raise TimeoutError("Reasoning synthesis timed out.")

        if self.simulate_error:
            raise RuntimeError("Reasoning synthesis LLM service outage.")

        if self.custom_synthesis:
            return self.custom_synthesis

        sections: list[str] = []
        action_requested = bool(
            re.search(
                r"\b(email|send|dispatch|create ticket|update|delete|restart)\b",
                user_question.lower(),
            )
        )

        if evidence:
            sections.append("Evidence considered:")
            for item in evidence[:5]:
                prefix = f"• [{item.source_type}]"
                if item.source_name:
                    prefix += f" {item.source_name}:"
                sections.append(f"{prefix} {item.content}")
        else:
            sections.append("No verified evidence was available.")

        if conflicts:
            sections.append("\nConflicting evidence detected:")
            for c in conflicts:
                sections.append(
                    f"• [{c.severity}] Discrepancy between {c.source_a} ('{c.claim_a}') and {c.source_b} ('{c.claim_b}')."
                )
            sections.append(
                "The available information is insufficient to determine which state is current."
            )

        if missing_information:
            sections.append("\nMissing information:")
            for m in missing_information:
                sections.append(f"• {m}")

        sections.append("\nConclusion:")
        if conflicts:
            conclusion = (
                "Due to conflicting evidence across sources, a definitive conclusion cannot be made without "
                "further manual verification."
            )
        elif missing_information and not evidence:
            conclusion = "I couldn't complete the analysis because the required records are not available in the authorized data."
        elif task_type == ReasoningTaskType.IMAGE_DATABASE_ANALYSIS.value:
            conclusion = (
                "The visual inspection evidence and database records have been cross-referenced. "
                "The findings indicate the observed component condition aligns with documented failure history."
            )
        elif task_type == ReasoningTaskType.DOCUMENT_DATABASE_ANALYSIS.value:
            conclusion = (
                "Based on the documented standard operating procedures and logged failure records, "
                "the documented procedure should be inspected first as specified in the technical manual."
            )
        elif (
            task_type == ReasoningTaskType.ROOT_CAUSE_ANALYSIS.value
            or task_type == ReasoningTaskType.TREND_ANALYSIS.value
        ):
            conclusion = (
                "Observed: Failure records indicate an elevated count for this period.\n"
                "Evidence: The recorded failure entries correlate primarily with the identified component.\n"
                "Inference: The component is a probable contributing factor to the recurring failures.\n"
                "Uncertainty: The available historical data establishes correlation but does not prove exclusive causation."
            )
        else:
            conclusion = "The available verified evidence supports the grounded analysis above without unsupported assumptions."

        sections.append(conclusion)

        if action_requested:
            sections.append(
                "\nAction Notice: You requested an external action (such as sending an email or updating records). "
                "The Reasoning Agent only performs read-only analysis. Performing external actions requires the Action Agent."
            )

        answer_text = "\n".join(sections)

        return {
            "answer": answer_text,
            "reasoning_summary": conclusion,
            "grounded": True,
        }


class MockAgentExecutor:
    """Mock agent executor for testing reasoning agent routing."""

    def __init__(
        self,
        agent_responses: dict[str, Any] | None = None,
        simulate_timeout_agents: set[str] | None = None,
        simulate_error_agents: set[str] | None = None,
        simulated_latency: float = 0.0,
    ):
        self.agent_responses = agent_responses or {}
        self.simulate_timeout_agents = simulate_timeout_agents or set()
        self.simulate_error_agents = simulate_error_agents or set()
        self.simulated_latency = simulated_latency
        self.executed_calls: list[dict[str, Any]] = []

    async def execute(
        self,
        agent_name: str,
        request: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        normalized_name = agent_name.strip().lower()

        self.executed_calls.append(
            {
                "agent_name": normalized_name,
                "request": request,
                "context": context,
            }
        )

        if normalized_name == "reasoning_agent":
            raise RecursionDepthExceededError("Reasoning Agent cannot invoke itself.")

        if (
            normalized_name not in ALLOWED_REASONING_AGENTS
            or normalized_name in PROHIBITED_AGENTS
        ):
            raise UnsafeAgentCallError(f"Agent '{agent_name}' is not in allowed list.")

        if not context.get("organization_id"):
            raise TenantSecurityViolationError(
                "Missing required authenticated organization_id in context."
            )

        if self.simulated_latency > 0:
            await asyncio.sleep(self.simulated_latency)

        if normalized_name in self.simulate_timeout_agents:
            raise AgentExecutionTimeoutError(
                f"Agent '{agent_name}' execution timed out."
            )

        if normalized_name in self.simulate_error_agents:
            raise RuntimeError(f"Downstream service outage in '{agent_name}'.")

        if normalized_name in self.agent_responses:
            res = self.agent_responses[normalized_name]
            if isinstance(res, Exception):
                raise res
            return res

        if normalized_name == "database_agent":
            return {
                "question": request.get("question", ""),
                "summary": "Database metrics retrieved successfully.",
                "columns": ["id", "status", "count"],
                "rows": [{"id": 1, "status": "active", "count": 10}],
                "row_count": 1,
                "query_executed": True,
                "confidence": 0.95,
            }
        if normalized_name == "rag_agent":
            return {
                "answer": "Relevant knowledge retrieved from company documents.",
                "grounded": True,
                "confidence": 0.94,
                "citations": [
                    {
                        "document_id": "doc-123",
                        "document_name": "Standard Operating Procedure",
                        "page_number": 2,
                        "chunk_id": "chunk-1",
                        "relevance_score": 0.92,
                    }
                ],
                "retrieved_chunks": 1,
            }
        if normalized_name == "vision_agent":
            return {
                "summary": "Visual inspection indicates normal component condition.",
                "answer": "The component shows normal wear without critical damage.",
                "findings": [
                    {
                        "observation": "Component surface intact",
                        "confidence": 0.95,
                        "severity": "info",
                    }
                ],
                "detected_objects": [{"label": "machine_part", "confidence": 0.96}],
                "confidence": 0.95,
            }
        if normalized_name == "document_agent":
            return {
                "title": "Technical Manual",
                "document_type": "TECHNICAL_MANUAL",
                "summary": "Operating procedures and troubleshooting guide.",
                "key_points": ["Inspect component X first upon error."],
                "confidence": 0.96,
                "sources": [{"page": 1, "section": "Troubleshooting"}],
            }

        return {"status": "success", "agent": normalized_name}


class MockLLMProvider:
    """Mock LLM provider for supervisor routing tests."""

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
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.simulated_latency_s > 0:
            await asyncio.sleep(self.simulated_latency_s)

        if self.simulate_timeout:
            raise TimeoutError("LLM inference timed out after timeout threshold.")

        if self.simulate_error:
            raise LLMProviderError("Simulated upstream LLM service outage.")

        if self.simulate_malformed:
            return {"corrupt": True, "syntax_error": None}

        if self.custom_response:
            return self.custom_response

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
            "explanation": "General enterprise inquiry resolved by Supervisor.",
        }


class MockVisionProvider:
    """Mock vision provider for offline vision testing."""

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
            raise TimeoutError("Vision inference request timed out.")

        if self.simulate_failure:
            raise VisionProviderError("Simulated upstream vision neural model outage.")

        if self.custom_response is not None:
            return self.custom_response

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
        elif task_type == "SAFETY_ANALYSIS" or "safety" in q_lower or "hazard" in q_lower:
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


class MockObjectDetector:
    """Deterministic mock object detector for unit tests."""

    def __init__(
        self,
        custom_detections: list[dict[str, Any]] | None = None,
        simulate_failure: bool = False,
        simulate_unavailable: bool = False,
    ):
        self.custom_detections = custom_detections
        self.simulate_failure = simulate_failure
        self.simulate_unavailable = simulate_unavailable

    async def detect(
        self, image_path: str | None = None, image_bytes: bytes | None = None
    ) -> tuple[list[dict[str, Any]], str, str | None]:
        if self.simulate_unavailable:
            return (
                [],
                ProcessorStatus.UNAVAILABLE.value,
                "Object detection is not configured for this deployment.",
            )

        if self.simulate_failure:
            return (
                [],
                ProcessorStatus.FAILED.value,
                "Detection model inference failure: upstream neural execution error.",
            )

        if self.custom_detections is not None:
            return self.custom_detections, ProcessorStatus.SUCCESS.value, None

        detections = [
            {
                "label": "machine_housing",
                "confidence": 0.94,
                "bbox": [120.0, 80.0, 540.0, 420.0],
                "class_id": 1,
            },
            {
                "label": "hydraulic_fitting",
                "confidence": 0.89,
                "bbox": [200.0, 150.0, 310.0, 260.0],
                "class_id": 2,
            },
        ]
        return detections, ProcessorStatus.SUCCESS.value, None


class MockOCRProvider:
    """Deterministic mock OCR provider for unit tests."""

    def __init__(
        self,
        custom_text: str | None = None,
        confidence: float = 0.94,
        regions: list[dict[str, Any]] | None = None,
        simulate_failure: bool = False,
        simulate_unavailable: bool = False,
    ):
        self.custom_text = custom_text
        self.confidence = confidence
        self.regions = regions
        self.simulate_failure = simulate_failure
        self.simulate_unavailable = simulate_unavailable

    async def extract_text(
        self, image_path: str | None = None, image_bytes: bytes | None = None
    ) -> dict[str, Any]:
        if self.simulate_unavailable:
            return {
                "text": "",
                "confidence": 0.0,
                "status": ProcessorStatus.UNAVAILABLE.value,
                "error": "OCR engine is not configured for this deployment.",
                "regions": [],
            }

        if self.simulate_failure:
            return {
                "text": "",
                "confidence": 0.0,
                "status": ProcessorStatus.FAILED.value,
                "error": "OCR extraction error: tesseract binary missing or corrupted.",
                "message": "Simulated OCR hardware/subsystem failure.",
                "regions": [],
            }

        text = self.custom_text if self.custom_text is not None else "Machine ID: M-102 Serial: SN-89321"
        confidence = self.confidence if (text and text.strip()) else 0.0
        regions = (
            self.regions
            if self.regions is not None
            else [
                {"text": "Machine ID: M-102", "bbox": [100.0, 80.0, 250.0, 40.0], "confidence": 0.95},
                {"text": "Serial: SN-89321", "bbox": [100.0, 130.0, 220.0, 40.0], "confidence": 0.93},
            ]
            if text
            else []
        )

        return {
            "text": text,
            "confidence": confidence,
            "status": ProcessorStatus.SUCCESS.value,
            "error": None,
            "regions": regions,
        }
