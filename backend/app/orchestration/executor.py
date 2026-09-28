"""
OmniAgent AI — Orchestration Agent Executor
Handles execution dispatching to registered agents, evidence normalization,
citation aggregation, conflict detection, timeout enforcement, and partial failure isolation.
"""

import asyncio
import time
from typing import Any

from app.core.logging import logger
from app.orchestration.errors import (
    ActionExecutionFailedError,
    ExecutionTimeoutError,
    TenantSecurityViolationError,
    UnauthorizedAgentCallError,
)
from app.orchestration.events import (
    EventRecorder,
    OrchestrationEventType,
    event_recorder as default_recorder,
)
from app.orchestration.limits import enforce_execution_timeout, get_orchestration_limits
from app.orchestration.policies import SafeTransitionPolicy, SecurityPolicy
from app.orchestration.registry import normalize_agent_name


class OrchestrationAgentExecutor:
    """Executes registered agents with strict tenant validation, latency tracking, and resilience."""

    def __init__(self, event_recorder: EventRecorder | None = None):
        self.events = event_recorder or default_recorder
        self.limits = get_orchestration_limits()

    async def execute_agent(
        self,
        agent_name: str,
        state: dict[str, Any],
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """
        Executes a specialist agent under verified security context.
        Returns a standardized dictionary containing output, status, evidence, and citations.
        """
        canonical_name = normalize_agent_name(agent_name)
        org_id = SecurityPolicy.enforce_tenant_context(state.get("organization_id"))
        user_id = str(state.get("user_id") or "anonymous")
        req_id = str(state.get("request_id") or "req_default")
        conv_id = state.get("conversation_id")
        session = state.get("session")

        # Record start event
        self.events.record(
            event_type=OrchestrationEventType.AGENT_STARTED,
            request_id=req_id,
            organization_id=org_id,
            conversation_id=conv_id,
            agent=canonical_name,
            status="STARTED",
        )

        start_time = time.time()
        timeout = timeout_seconds or 30.0

        try:
            raw_result = await asyncio.wait_for(
                self._dispatch(canonical_name, state, org_id, user_id, req_id, conv_id, session),
                timeout=timeout,
            )
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            evidence, citations = self._extract_evidence_and_citations(canonical_name, raw_result)
            confidence = self._extract_confidence(raw_result)

            self.events.record(
                event_type=OrchestrationEventType.AGENT_COMPLETED,
                request_id=req_id,
                organization_id=org_id,
                conversation_id=conv_id,
                agent=canonical_name,
                status="COMPLETED",
                metadata={"elapsed_ms": elapsed_ms, "confidence": confidence},
            )

            return {
                "agent": canonical_name,
                "status": "completed",
                "output": raw_result,
                "confidence": confidence,
                "evidence": evidence,
                "citations": citations,
                "elapsed_ms": elapsed_ms,
                "error": None,
            }

        except asyncio.TimeoutError:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            logger.error("agent_execution_timeout", agent=canonical_name, request_id=req_id)
            self.events.record(
                event_type=OrchestrationEventType.AGENT_FAILED,
                request_id=req_id,
                organization_id=org_id,
                conversation_id=conv_id,
                agent=canonical_name,
                status="FAILED",
                metadata={"error": "Agent execution timed out", "elapsed_ms": elapsed_ms},
            )
            return {
                "agent": canonical_name,
                "status": "failed",
                "output": {},
                "confidence": 0.0,
                "evidence": [],
                "citations": [],
                "elapsed_ms": elapsed_ms,
                "error": f"Agent '{canonical_name}' timed out after {timeout} seconds.",
            }

        except Exception as exc:  # noqa: BLE001
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            logger.error("agent_execution_error", agent=canonical_name, request_id=req_id, error=str(exc))
            self.events.record(
                event_type=OrchestrationEventType.AGENT_FAILED,
                request_id=req_id,
                organization_id=org_id,
                conversation_id=conv_id,
                agent=canonical_name,
                status="FAILED",
                metadata={"error": str(exc), "elapsed_ms": elapsed_ms},
            )
            return {
                "agent": canonical_name,
                "status": "failed",
                "output": {},
                "confidence": 0.0,
                "evidence": [],
                "citations": [],
                "elapsed_ms": elapsed_ms,
                "error": str(exc),
            }

    async def _dispatch(
        self,
        agent_name: str,
        state: dict[str, Any],
        org_id: str,
        user_id: str,
        req_id: str,
        conv_id: str | None,
        session: Any,
    ) -> Any:
        prompt = state.get("user_message", "")
        context = dict(state.get("context") or {})

        if agent_name == "supervisor":
            from agents.supervisor.agent import SupervisorAgent
            supervisor = SupervisorAgent()
            res = await supervisor.analyze(
                message=prompt,
                conversation_id=conv_id,
                user_id=user_id,
                organization_id=org_id,
                request_id=req_id,
                context=context,
            )
            return res.model_dump() if hasattr(res, "model_dump") else res

        elif agent_name == "rag_agent":
            from agents.rag.agent import RAGAgent
            rag = RAGAgent()
            doc_id = context.get("document_id")
            res = await rag.query(
                question=prompt,
                organization_id=org_id,
                user_id=user_id,
                conversation_id=conv_id,
                document_id=str(doc_id) if doc_id else None,
                request_id=req_id,
            )
            return res.model_dump() if hasattr(res, "model_dump") else res

        elif agent_name == "database_agent":
            from agents.database.agent import DatabaseAgent
            db_agent = DatabaseAgent(session=session)
            res = await db_agent.query(
                question=prompt,
                organization_id=org_id,
                user_id=user_id,
                conversation_id=conv_id or "",
                request_id=req_id,
                session=session,
            )
            return res.model_dump() if hasattr(res, "model_dump") else res

        elif agent_name == "vision_agent":
            from agents.vision.agent import VisionAgent
            vision = VisionAgent()
            # Check attachments for image bytes or path
            image_id = context.get("image_id", "default_img")
            image_bytes = context.get("image_bytes")
            image_path = context.get("image_path")

            attachments = state.get("attachments") or []
            for att in attachments:
                if isinstance(att, dict) and att.get("type") == "image":
                    if att.get("id"):
                        image_id = att["id"]
                    if att.get("content_b64"):
                        import base64
                        try:
                            image_bytes = base64.b64decode(att["content_b64"])
                        except Exception:
                            pass
                    if att.get("url"):
                        image_path = att["url"]

            res = await vision.analyze(
                image_id=str(image_id),
                question=prompt,
                image_bytes=image_bytes,
                image_path=image_path,
                user_id=user_id,
                organization_id=org_id,
                conversation_id=conv_id,
                request_id=req_id,
            )
            return res.model_dump() if hasattr(res, "model_dump") else res

        elif agent_name == "document_agent":
            from agents.document.agent import DocumentAgent
            doc_agent = DocumentAgent()
            doc_id = context.get("document_id", "default_doc")
            file_bytes = context.get("file_bytes")
            file_path = context.get("file_path")

            attachments = state.get("attachments") or []
            for att in attachments:
                if isinstance(att, dict) and att.get("type") in ("document", "file"):
                    if att.get("id"):
                        doc_id = att["id"]
                    if att.get("content_b64"):
                        import base64
                        try:
                            file_bytes = base64.b64decode(att["content_b64"])
                        except Exception:
                            pass

            res = await doc_agent.analyze(
                document_id=str(doc_id),
                file_bytes=file_bytes,
                file_path=file_path,
                filename=context.get("filename", "document.pdf"),
                task=context.get("task", "summarize"),
                query=prompt,
                user_id=user_id,
                organization_id=org_id,
                request_id=req_id,
            )
            return res.model_dump() if hasattr(res, "model_dump") else res

        elif agent_name == "reasoning_agent":
            from agents.reasoning.agent import ReasoningAgent
            reasoning = ReasoningAgent()
            res = await reasoning.analyze(
                question=prompt,
                organization_id=org_id,
                user_id=user_id,
                conversation_id=conv_id,
                request_id=req_id,
                image_id=context.get("image_id"),
                document_id=context.get("document_id"),
                context=context,
            )
            return res.model_dump() if hasattr(res, "model_dump") else res

        elif agent_name == "action_agent":
            from agents.action.agent import ActionAgent
            from agents.action.schemas import ActionContext, ActionRequest
            action_agent = ActionAgent(session=session)

            action_type = state.get("action_type") or context.get("action_type") or "send_notification"
            input_data = state.get("action_input") or context.get("action_input") or {}
            approval_id = state.get("approval_id")

            act_context = ActionContext(
                user_id=user_id,
                organization_id=org_id,
                user_role=context.get("user_role", "Operator"),
                user_permissions=context.get("user_permissions", []),
                request_id=req_id,
                conversation_id=conv_id,
            )
            act_request = ActionRequest(
                action_type=action_type,
                input=input_data,
                approval_id=approval_id,
                reason=context.get("reason", "Action requested via orchestration workflow"),
            )
            res = await action_agent.execute(act_request, act_context, session=session)
            return res.model_dump() if hasattr(res, "model_dump") else res

        raise UnauthorizedAgentCallError(f"Agent '{agent_name}' is not authorized to execute.")

    def _extract_evidence_and_citations(
        self, agent_name: str, raw_output: Any
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        evidence = []
        citations = []

        if not isinstance(raw_output, dict):
            return evidence, citations

        if agent_name == "rag_agent":
            for c in raw_output.get("citations", []):
                citations.append({
                    "document_id": c.get("document_id", ""),
                    "document_name": c.get("document_name", "Knowledge Document"),
                    "page_number": c.get("page_number"),
                    "section": c.get("section"),
                    "relevance_score": c.get("relevance_score"),
                })
                evidence.append({
                    "source_type": "rag",
                    "source_id": c.get("document_id", ""),
                    "source_name": c.get("document_name", "Knowledge Document"),
                    "content": c.get("chunk_text") or c.get("excerpt") or raw_output.get("answer", ""),
                    "page_number": c.get("page_number"),
                    "confidence": raw_output.get("confidence", 0.95),
                    "metadata": {"relevance_score": c.get("relevance_score")},
                })

        elif agent_name == "database_agent":
            summary = raw_output.get("summary", "")
            rows = raw_output.get("rows", [])
            evidence.append({
                "source_type": "database",
                "source_id": "sql_query",
                "source_name": "Enterprise Production Database",
                "content": f"{summary}. Rows returned: {len(rows)}",
                "confidence": raw_output.get("confidence", 1.0),
                "metadata": {"columns": raw_output.get("columns", []), "row_count": len(rows)},
            })

        elif agent_name == "vision_agent":
            findings = raw_output.get("findings", [])
            answer = raw_output.get("answer", "")
            summary = raw_output.get("summary", "")
            content_desc = summary or answer
            if findings:
                finding_texts = [f.get("observation", "") for f in findings if isinstance(f, dict)]
                if finding_texts:
                    content_desc += " | " + "; ".join(finding_texts)

            evidence.append({
                "source_type": "vision",
                "source_id": raw_output.get("image_id", "image_inspection"),
                "source_name": "Visual Inspection",
                "content": content_desc,
                "confidence": raw_output.get("confidence", 0.95),
                "metadata": {
                    "detected_objects": [d.get("label") for d in raw_output.get("detected_objects", []) if isinstance(d, dict)],
                    "ocr_text": raw_output.get("ocr_result", {}).get("text", "") if isinstance(raw_output.get("ocr_result"), dict) else "",
                },
            })

        elif agent_name == "document_agent":
            evidence.append({
                "source_type": "document",
                "source_id": raw_output.get("document_id", "doc"),
                "source_name": raw_output.get("title", "Document Artifact"),
                "content": raw_output.get("summary", ""),
                "confidence": raw_output.get("confidence", 0.95),
                "metadata": {
                    "document_type": raw_output.get("document_type", "UNKNOWN"),
                    "key_points": raw_output.get("key_points", []),
                },
            })

        elif agent_name == "reasoning_agent":
            for ev in raw_output.get("evidence", []):
                if isinstance(ev, dict):
                    evidence.append(ev)

        return evidence, citations

    def _extract_confidence(self, raw_output: Any) -> float:
        if isinstance(raw_output, dict):
            conf = raw_output.get("confidence")
            if isinstance(conf, (int, float)):
                return float(conf)
        return 1.0


def detect_evidence_conflicts(evidence_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Evaluates evidence collected across distinct sources to detect contradictory facts.
    Never merges conflicting evidence silently.
    """
    conflicts = []
    if len(evidence_items) < 2:
        return conflicts

    # Detect high-severity polarity discrepancies between sources
    sources = {}
    for ev in evidence_items:
        st = ev.get("source_type")
        sources.setdefault(st, []).append(ev)

    # Check for direct conflicts (e.g. failure detected by vision vs database saying normal)
    vision_items = sources.get("vision", [])
    db_items = sources.get("database", [])

    for v in vision_items:
        v_content = v.get("content", "").lower()
        for d in db_items:
            d_content = d.get("content", "").lower()
            if ("crack" in v_content or "fail" in v_content or "leak" in v_content or "issue" in v_content) and \
               ("passed" in d_content or "normal" in d_content or "no defect" in d_content):
                conflicts.append({
                    "source_a": "Visual Inspection",
                    "source_b": "Production Database",
                    "claim_a": v.get("content", "")[:120],
                    "claim_b": d.get("content", "")[:120],
                    "severity": "HIGH",
                    "note": "Vision detected component anomaly while database records normal operational status.",
                })

    return conflicts


# Default singleton instance
executor = OrchestrationAgentExecutor()

