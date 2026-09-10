import time
import uuid
from typing import Any

from agents.document.graph import build_document_graph
from agents.document.nodes import (
    classify_document_node,
    extract_text_node,
    normalize_content_node,
    understand_document_node,
    validate_document_node,
    validate_result_node,
)
from agents.document.providers import (
    BaseDocumentLLMProvider,
    get_default_document_llm_provider,
)
from agents.document.schemas import (
    DocumentAnalysisResult,
    DocumentPage,
    DocumentType,
)
from agents.document.state import DocumentState

try:
    from app.core.logging import logger
except ImportError:
    try:
        from backend.app.core.logging import logger
    except ImportError:
        import logging
        logger = logging.getLogger("omniagent.document")


class DocumentAgent:
    """
    Enterprise Multimodal AI Employee: Document Understanding Specialist.
    Executes deep document parsing, validation, classification, and structured extraction
    across PDF, DOCX, and TXT artifacts.
    """

    def __init__(self, provider: BaseDocumentLLMProvider | None = None):
        self.provider = provider or get_default_document_llm_provider()
        self._compiled_graph = build_document_graph(provider=self.provider)

    async def analyze(
        self,
        document_id: str,
        file_bytes: bytes | None = None,
        file_path: str | None = None,
        filename: str = "document.bin",
        mime_type: str | None = None,
        task: str = "summarize",
        query: str | None = None,
        user_id: str | None = None,
        organization_id: str | None = None,
        request_id: str | None = None
    ) -> DocumentAnalysisResult:
        """
        Main entrypoint for document intelligence.
        Executes LangGraph pipeline with strict safety, citation tracking, and audit logging.
        """
        start_time = time.time()
        req_id = request_id or str(uuid.uuid4())
        u_id = user_id or "anonymous"
        org_id = organization_id or "default_org"

        initial_state: DocumentState = {
            "request_id": req_id,
            "user_id": u_id,
            "organization_id": org_id,
            "document_id": str(document_id),
            "filename": filename,
            "file_path": file_path or "",
            "file_bytes": file_bytes,
            "mime_type": mime_type or "",
            "file_size": len(file_bytes) if file_bytes else 0,
            "task": task,
            "query": query,
            "status": "INITIALIZED",
            "error": None,
            "confidence": 0.0,
            "warnings": [],
            "needs_ocr": False,
            "pages": [],
            "sections": [],
            "tables": []
        }

        try:
            if self._compiled_graph is not None:
                final_state = await self._compiled_graph.ainvoke(initial_state)
            else:
                final_state = await self._run_sequential(initial_state)

            latency_ms = round((time.time() - start_time) * 1000, 2)
            raw_result = final_state.get("result", {})

            # Construct validated Pydantic model
            pages_data = [
                DocumentPage(**p) if isinstance(p, dict) else p
                for p in raw_result.get("pages", [])
            ]

            result = DocumentAnalysisResult(
                document_id=str(document_id),
                document_type=raw_result.get("document_type", final_state.get("document_type", DocumentType.UNKNOWN.value)),
                title=raw_result.get("title", "Document"),
                summary=raw_result.get("summary", ""),
                key_points=raw_result.get("key_points", []),
                entities=raw_result.get("entities", {}),
                structured_data=raw_result.get("structured_data", {}),
                pages=pages_data,
                sources=raw_result.get("sources", []),
                confidence=final_state.get("confidence", raw_result.get("confidence", 1.0)),
                needs_ocr=raw_result.get("needs_ocr", final_state.get("needs_ocr", False)),
                warnings=raw_result.get("warnings", final_state.get("warnings", [])),
                execution_time_ms=latency_ms
            )

            # Audit logging: execution metadata only, no secrets or raw document dumps
            if hasattr(logger, "info"):
                logger.info(
                    "document_analysis_completed",
                    request_id=req_id,
                    user_id=u_id,
                    organization_id=org_id,
                    document_id=str(document_id),
                    agent_name="document",
                    document_type=result.document_type,
                    confidence=result.confidence,
                    needs_ocr=result.needs_ocr,
                    status=final_state.get("status", "SUCCESS"),
                    processing_time_ms=latency_ms
                )

            return result

        except Exception as exc:  # noqa: BLE001
            latency_ms = round((time.time() - start_time) * 1000, 2)
            if hasattr(logger, "error"):
                logger.error(
                    "document_analysis_failed",
                    request_id=req_id,
                    user_id=u_id,
                    organization_id=org_id,
                    document_id=str(document_id),
                    error=str(exc),
                    processing_time_ms=latency_ms
                )
            return DocumentAnalysisResult(
                document_id=str(document_id),
                document_type=DocumentType.UNKNOWN.value,
                title="Analysis Failure",
                summary="An error occurred while processing the document.",
                key_points=[],
                entities={},
                structured_data={},
                pages=[],
                sources=[],
                confidence=0.0,
                needs_ocr=False,
                warnings=[str(exc)],
                execution_time_ms=latency_ms
            )

    async def _run_sequential(self, state: DocumentState) -> DocumentState:
        """Sequential fallback runner if LangGraph compilation is unavailable."""
        current = dict(state)

        # 1. Validate
        u = await validate_document_node(current)
        current.update(u)
        if current.get("status") == "FAILED_VALIDATION":
            u = await validate_result_node(current)
            current.update(u)
            return current

        # 2. Extract
        u = await extract_text_node(current)
        current.update(u)
        if current.get("status") == "FAILED_EXTRACTION":
            u = await validate_result_node(current)
            current.update(u)
            return current

        # 3. Normalize
        u = await normalize_content_node(current)
        current.update(u)

        # 4. Classify
        u = await classify_document_node(current)
        current.update(u)

        # 5. Understand
        u = await understand_document_node(current, provider=self.provider)
        current.update(u)

        # 6. Validate Result
        u = await validate_result_node(current)
        current.update(u)

        return current

    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Legacy/multi-agent graph hook maintaining compatibility with agents/graph/nodes.py.
        """
        doc_id = state.get("document_id") or str(uuid.uuid4())
        file_bytes = state.get("file_bytes")
        file_path = state.get("file_path")
        text_content = state.get("task_goal") or state.get("extracted_text")

        if not file_bytes and not file_path and text_content:
            file_bytes = text_content.encode("utf-8")

        if file_bytes or file_path:
            result = await self.analyze(
                document_id=doc_id,
                file_bytes=file_bytes,
                file_path=file_path,
                filename=state.get("filename", "document.txt"),
                task=state.get("task", "summarize")
            )
            return {
                "status": "success",
                "agent": "document",
                "result": result.model_dump()
            }

        return {
            "status": "success",
            "agent": "document",
            "result": "Document agent ready. Please provide document_id or file."
        }
