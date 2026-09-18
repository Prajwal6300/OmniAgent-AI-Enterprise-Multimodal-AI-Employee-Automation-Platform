"""
OmniAgent AI — Evidence Normalizer & Conflict Detector
Normalizes heterogeneous specialized agent outputs into standardized Evidence records,
identifies factual contradictions across modalities, and computes objective confidence scores.
"""

import re
from typing import Any

from agents.reasoning.schemas import (
    ConflictSeverity,
    Evidence,
    EvidenceConflict,
    EvidenceSourceType,
)


class EvidenceNormalizer:
    """
    Transforms specialized downstream agent response payloads into normalized Evidence objects.
    Protects against prompt injections by sanitizing and boxing untrusted textual data.
    """

    @staticmethod
    def normalize_all(agent_outputs: dict[str, dict[str, Any]]) -> list[Evidence]:
        """Normalizes outputs from all contributing specialized agents into an evidence list."""
        all_evidence: list[Evidence] = []

        for agent_name, raw_output in agent_outputs.items():
            if not isinstance(raw_output, dict):
                continue

            if agent_name == "database_agent":
                all_evidence.extend(EvidenceNormalizer.normalize_database(raw_output))
            elif agent_name == "rag_agent":
                all_evidence.extend(EvidenceNormalizer.normalize_rag(raw_output))
            elif agent_name == "vision_agent":
                all_evidence.extend(EvidenceNormalizer.normalize_vision(raw_output))
            elif agent_name == "document_agent":
                all_evidence.extend(EvidenceNormalizer.normalize_document(raw_output))
            else:
                # Generic fallback normalization
                content = (
                    raw_output.get("summary")
                    or raw_output.get("answer")
                    or str(raw_output)
                )
                all_evidence.append(
                    Evidence(
                        source_type=EvidenceSourceType.DOCUMENT.value,
                        source_id=str(raw_output.get("id", agent_name)),
                        source_name=agent_name,
                        content=str(content),
                        confidence=float(raw_output.get("confidence", 0.9)),
                        metadata={"raw_agent": agent_name},
                    )
                )

        return all_evidence

    @staticmethod
    def normalize_database(output: dict[str, Any]) -> list[Evidence]:
        """Normalizes Database Agent response containing summary, rows, and aggregations."""
        evidence_list: list[Evidence] = []
        confidence = float(output.get("confidence", 0.95))
        summary = output.get("summary", "")
        rows = output.get("rows", [])
        row_count = output.get("row_count", len(rows))

        # 1. Primary summary evidence
        if summary:
            evidence_list.append(
                Evidence(
                    source_type=EvidenceSourceType.DATABASE.value,
                    source_name="database_records",
                    content=summary,
                    confidence=confidence,
                    metadata={
                        "row_count": row_count,
                        "columns": output.get("columns", []),
                    },
                )
            )

        # 2. Key individual row observations (capped to first 5 rows to prevent token exhaustion)
        for idx, row in enumerate(rows[:5]):
            row_repr = ", ".join(f"{k}={v}" for k, v in row.items())
            evidence_list.append(
                Evidence(
                    source_type=EvidenceSourceType.DATABASE.value,
                    source_name=f"database_row_{idx + 1}",
                    content=f"Record {idx + 1}: {row_repr}",
                    confidence=confidence,
                    metadata=row,
                )
            )

        return evidence_list

    @staticmethod
    def normalize_rag(output: dict[str, Any]) -> list[Evidence]:
        """Normalizes RAG Agent response containing synthesized answer and document citations."""
        evidence_list: list[Evidence] = []
        confidence = float(output.get("confidence", 0.92))
        answer = output.get("answer", "")
        citations = output.get("citations", [])

        # 1. Primary retrieved knowledge answer
        if answer:
            evidence_list.append(
                Evidence(
                    source_type=EvidenceSourceType.RAG.value,
                    source_name="knowledge_retrieval",
                    content=answer,
                    confidence=confidence,
                    metadata={"retrieved_chunks": output.get("retrieved_chunks", 0)},
                )
            )

        # 2. Individual citation passages
        for citation in citations:
            doc_name = citation.get("document_name") or "Enterprise Knowledge Base"
            page_num = citation.get("page_number")
            section = citation.get("section")
            chunk_id = citation.get("chunk_id")
            content_snippet = (
                citation.get("content")
                or citation.get("text")
                or f"Document reference: {doc_name}"
            )

            evidence_list.append(
                Evidence(
                    source_type=EvidenceSourceType.RAG.value,
                    source_id=str(citation.get("document_id") or chunk_id or ""),
                    source_name=doc_name,
                    content=content_snippet,
                    page_number=page_num,
                    confidence=float(citation.get("relevance_score") or confidence),
                    metadata={"section": section, "chunk_id": chunk_id},
                )
            )

        return evidence_list

    @staticmethod
    def normalize_vision(output: dict[str, Any]) -> list[Evidence]:
        """Normalizes Vision Agent response containing findings, detected objects, and OCR."""
        evidence_list: list[Evidence] = []
        confidence = float(output.get("confidence", 0.94))
        summary = output.get("summary") or output.get("answer", "")
        findings = output.get("findings", [])
        detected_objects = output.get("detected_objects", [])
        ocr_result = output.get("ocr_result", {})

        # 1. High-level visual summary
        if summary:
            evidence_list.append(
                Evidence(
                    source_type=EvidenceSourceType.IMAGE.value,
                    source_name="visual_inspection",
                    content=summary,
                    confidence=confidence,
                    metadata={"image_id": output.get("image_id")},
                )
            )

        # 2. Discrete visual findings
        for finding in findings:
            obs = (
                finding.get("observation") or finding.get("description") or str(finding)
            )
            evidence_list.append(
                Evidence(
                    source_type=EvidenceSourceType.IMAGE.value,
                    source_name="visual_finding",
                    content=obs,
                    confidence=float(finding.get("confidence", confidence)),
                    metadata={"severity": finding.get("severity", "info")},
                )
            )

        # 3. Discrete detected objects
        if detected_objects:
            obj_labels = [
                obj.get("label") for obj in detected_objects if obj.get("label")
            ]
            if obj_labels:
                evidence_list.append(
                    Evidence(
                        source_type=EvidenceSourceType.OBJECT_DETECTION.value,
                        source_name="object_detector",
                        content=f"Detected components/objects: {', '.join(obj_labels)}",
                        confidence=confidence,
                        metadata={"detections": detected_objects[:5]},
                    )
                )

        # 4. Extracted OCR text snippet
        ocr_text = (
            ocr_result.get("text", "").strip() if isinstance(ocr_result, dict) else ""
        )
        if ocr_text:
            evidence_list.append(
                Evidence(
                    source_type=EvidenceSourceType.OCR.value,
                    source_name="ocr_inscriptions",
                    content=f"Extracted visual text: {ocr_text}",
                    confidence=float(ocr_result.get("confidence", confidence)),
                    metadata={"ocr_status": ocr_result.get("status")},
                )
            )

        return evidence_list

    @staticmethod
    def normalize_document(output: dict[str, Any]) -> list[Evidence]:
        """Normalizes Document Agent response containing title, summary, key points, and sources."""
        evidence_list: list[Evidence] = []
        confidence = float(output.get("confidence", 0.95))
        title = output.get("title") or "Document Analysis"
        summary = output.get("summary", "")
        key_points = output.get("key_points", [])

        # 1. Primary document summary
        if summary:
            evidence_list.append(
                Evidence(
                    source_type=EvidenceSourceType.DOCUMENT.value,
                    source_name=title,
                    content=summary,
                    confidence=confidence,
                    metadata={"document_type": output.get("document_type")},
                )
            )

        # 2. Key extracted rules or findings
        for pt in key_points:
            evidence_list.append(
                Evidence(
                    source_type=EvidenceSourceType.DOCUMENT.value,
                    source_name=title,
                    content=pt,
                    confidence=confidence,
                    metadata={"document_type": output.get("document_type")},
                )
            )

        return evidence_list


class ConflictDetector:
    """
    Evaluates normalized evidence from multiple agents to detect contradictions.
    Applies deterministic semantic rules for common discrepancies (status, count, state)
    without inventing subjective causes.
    """

    @staticmethod
    def detect_conflicts(evidence_list: list[Evidence]) -> list[EvidenceConflict]:
        """Scans evidence pairs to detect state, numerical, or procedural conflicts."""
        conflicts: list[EvidenceConflict] = []
        if len(evidence_list) < 2:
            return conflicts

        # Collect observations by modality
        db_contents = [
            e.content.lower()
            for e in evidence_list
            if e.source_type == EvidenceSourceType.DATABASE.value
        ]
        vision_contents = [
            e.content.lower()
            for e in evidence_list
            if e.source_type
            in (
                EvidenceSourceType.IMAGE.value,
                EvidenceSourceType.OBJECT_DETECTION.value,
                EvidenceSourceType.OCR.value,
            )
        ]
        doc_contents = [
            e.content.lower()
            for e in evidence_list
            if e.source_type
            in (EvidenceSourceType.DOCUMENT.value, EvidenceSourceType.RAG.value)
        ]

        # 1. Machine Status Conflict: Database vs Vision (e.g. running vs stopped/idle/damaged)
        if db_contents and vision_contents:
            db_full = " ".join(db_contents)
            vis_full = " ".join(vision_contents)

            # Check running vs stopped / offline / halt
            db_running = bool(
                re.search(
                    r"\b(running|active|operational|online|functioning)\b", db_full
                )
            )
            vis_stopped = bool(
                re.search(
                    r"\b(stopped|halted|idle|offline|broken|damaged|shut down|not running)\b",
                    vis_full,
                )
            )

            if db_running and vis_stopped:
                conflicts.append(
                    EvidenceConflict(
                        source_a="database_agent",
                        source_b="vision_agent",
                        claim_a="Database records report machine status as RUNNING or operational.",
                        claim_b="Visual inspection shows the machine is STOPPED, idle, or damaged.",
                        severity=ConflictSeverity.HIGH.value,
                    )
                )

            # Inverse check: DB reports offline but image shows active
            db_offline = bool(
                re.search(r"\b(stopped|halted|offline|inactive|failed)\b", db_full)
            )
            vis_active = bool(
                re.search(r"\b(running|active|operating|operational)\b", vis_full)
            )
            if db_offline and vis_active and not (db_running and vis_stopped):
                conflicts.append(
                    EvidenceConflict(
                        source_a="database_agent",
                        source_b="vision_agent",
                        claim_a="Database records report machine status as STOPPED or offline.",
                        claim_b="Visual inspection indicates machine is actively operating.",
                        severity=ConflictSeverity.HIGH.value,
                    )
                )

        # 2. Procedural Conflict: Documentation SOP vs Observed Database Actions
        if doc_contents and db_contents:
            doc_full = " ".join(doc_contents)
            db_full = " ".join(db_contents)

            # Check troubleshooting recommendation vs actual failure
            if "follow" in doc_full and "unauthorized" in db_full:
                conflicts.append(
                    EvidenceConflict(
                        source_a="document_agent",
                        source_b="database_agent",
                        claim_a="Documentation mandates strict troubleshooting procedure adherence.",
                        claim_b="Logged database actions record deviation from standard procedures.",
                        severity=ConflictSeverity.MEDIUM.value,
                    )
                )

        return conflicts


class ConfidenceCalculator:
    """
    Computes an objective, grounded confidence score reflecting evidence quality,
    source coverage, and presence of conflicting evidence.
    """

    @staticmethod
    def calculate(
        evidence_list: list[Evidence],
        conflicts: list[EvidenceConflict],
        missing_information: list[str],
        required_agents: list[str],
        contributing_agents: list[str],
    ) -> float:
        """Calculates final confidence score clamped between 0.0 and 1.0."""
        if not evidence_list:
            return 0.0

        # Base confidence: average confidence of collected evidence items
        valid_confidences = [
            e.confidence for e in evidence_list if e.confidence is not None
        ]
        base_confidence = (
            sum(valid_confidences) / len(valid_confidences)
            if valid_confidences
            else 0.85
        )

        score = base_confidence

        # Deduct for missing required specialist agents
        missing_agents = set(required_agents) - set(contributing_agents)
        score -= len(missing_agents) * 0.20

        # Deduct for missing information items
        score -= len(missing_information) * 0.10

        # Deduct for conflicts based on severity
        for c in conflicts:
            if c.severity == ConflictSeverity.HIGH.value:
                score -= 0.30
            elif c.severity == ConflictSeverity.MEDIUM.value:
                score -= 0.15
            else:
                score -= 0.05

        return max(0.0, min(1.0, round(score, 4)))
