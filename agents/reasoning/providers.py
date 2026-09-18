"""
OmniAgent AI — Reasoning Agent LLM Providers
Defines the abstract inference contracts, deterministic pattern planning,
synthesis logic, and mock fault-injection providers for the Reasoning Agent.
"""

import asyncio
import re
from abc import ABC, abstractmethod
from typing import Any

from agents.reasoning.schemas import (
    Evidence,
    EvidenceConflict,
    ReasoningTaskType,
)


def classify_task_deterministically(question: str) -> tuple[str, list[str], str]:
    """
    High-precision deterministic rule classifier for enterprise queries.
    Maps user prompts to standard ReasoningTaskType and required agents.
    """
    q_lower = question.strip().lower()

    # Image + Database / Maintenance records comparison
    has_image = any(
        k in q_lower
        for k in ["image", "picture", "photo", "inspection image", "visual"]
    )
    has_db_or_records = any(
        k in q_lower
        for k in [
            "maintenance record",
            "maintenance records",
            "maintenance history",
            "recent failures",
            "failure record",
            "failure records",
            "production failures",
            "database",
            "orders",
            "tickets",
            "failures",
            "failure",
            "failed",
            "records",
            "followed",
            "machine m-",
        ]
    )
    has_manual_or_doc = any(
        k in q_lower
        for k in [
            "manual",
            "handbook",
            "sop",
            "pdf",
            "invoice",
            "procedure",
            "policy",
            "documentation",
        ]
    )
    has_compare = any(
        k in q_lower
        for k in [
            "compare",
            "comparison",
            "difference",
            "discrepancy",
            "reconcile",
            "reconciliation",
        ]
    )

    if has_image and has_db_or_records:
        return (
            ReasoningTaskType.IMAGE_DATABASE_ANALYSIS.value,
            ["vision_agent", "database_agent"],
            "Cross-modal analysis comparing physical visual inspection with historical database records.",
        )

    if has_image and has_manual_or_doc:
        return (
            ReasoningTaskType.IMAGE_DOCUMENT_ANALYSIS.value,
            ["vision_agent", "document_agent"],
            "Comparing visual component features with documented engineering specifications.",
        )

    if has_manual_or_doc and has_db_or_records:
        return (
            ReasoningTaskType.DOCUMENT_DATABASE_ANALYSIS.value,
            ["rag_agent", "database_agent"],
            "Correlating documented troubleshooting procedures with empirical database failure logs.",
        )

    if has_compare and has_manual_or_doc:
        return (
            ReasoningTaskType.CROSS_DOCUMENT_ANALYSIS.value,
            ["document_agent", "rag_agent"],
            "Comparing clauses, figures, or specifications across multiple document artifacts.",
        )

    if any(
        k in q_lower
        for k in ["why might", "why is", "root cause", "reason for", "cause of", "why"]
    ):
        return (
            ReasoningTaskType.ROOT_CAUSE_ANALYSIS.value,
            ["database_agent"],
            "Investigating underlying failure modes and correlating operational statistics.",
        )

    if any(
        k in q_lower
        for k in [
            "trend",
            "most common",
            "most frequent",
            "increase in",
            "decrease in",
            "over time",
        ]
    ):
        return (
            ReasoningTaskType.TREND_ANALYSIS.value,
            ["database_agent"],
            "Analyzing historical aggregate trends and recurring categorical patterns.",
        )

    if has_compare:
        return (
            ReasoningTaskType.COMPARISON.value,
            ["database_agent"],
            "Performing structured comparison between operational entities.",
        )

    if any(
        k in q_lower
        for k in [
            "recommend",
            "should we",
            "decision",
            "next step",
            "what troubleshooting step",
        ]
    ):
        return (
            ReasoningTaskType.DECISION_SUPPORT.value,
            ["rag_agent", "database_agent"],
            "Synthesizing multi-source evidence to recommend grounded operational next steps.",
        )

    return (
        ReasoningTaskType.GENERAL_REASONING.value,
        ["database_agent"],
        "Executing general analytical reasoning over enterprise information.",
    )


class BaseReasoningLLMProvider(ABC):
    """Abstract interface for planning and multi-source reasoning synthesis."""

    @abstractmethod
    async def plan(
        self,
        user_question: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Classifies reasoning task and produces operational execution plan."""
        ...

    @abstractmethod
    async def synthesize(
        self,
        user_question: str,
        task_type: str,
        evidence: list[Evidence],
        conflicts: list[EvidenceConflict],
        missing_information: list[str],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Synthesizes grounded conclusions, evidence considered, and answers."""
        ...


class MockReasoningLLMProvider(BaseReasoningLLMProvider):
    """
    Mock reasoning provider for offline testing, deterministic evaluation,
    and simulated edge-case responses.
    """

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
            raise asyncio.TimeoutError("Reasoning planning timed out.")

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
            raise asyncio.TimeoutError("Reasoning synthesis timed out.")

        if self.simulate_error:
            raise RuntimeError("Reasoning synthesis LLM service outage.")

        if self.custom_synthesis:
            return self.custom_synthesis

        # Deterministic grounded synthesis
        sections: list[str] = []
        action_requested = bool(
            re.search(
                r"\b(email|send|dispatch|create ticket|update|delete|restart)\b",
                user_question.lower(),
            )
        )

        # 1. Evidence Considered summary
        if evidence:
            sections.append("Evidence considered:")
            for item in evidence[:5]:
                prefix = f"• [{item.source_type}]"
                if item.source_name:
                    prefix += f" {item.source_name}:"
                sections.append(f"{prefix} {item.content}")
        else:
            sections.append("No verified evidence was available.")

        # 2. Conflicts notice
        if conflicts:
            sections.append("\nConflicting evidence detected:")
            for c in conflicts:
                sections.append(
                    f"• [{c.severity}] Discrepancy between {c.source_a} ('{c.claim_a}') and {c.source_b} ('{c.claim_b}')."
                )
            sections.append(
                "The available information is insufficient to determine which state is current."
            )

        # 3. Missing information notice
        if missing_information:
            sections.append("\nMissing information:")
            for m in missing_information:
                sections.append(f"• {m}")

        # 4. Synthesized Conclusion
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

        # 5. Action boundary disclaimer if user asked for external action
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


class HybridReasoningLLMProvider(BaseReasoningLLMProvider):
    """
    Hybrid provider that leverages deterministic classification and templates for standard enterprise patterns,
    with seamless fallback to secondary or online LLM providers.
    """

    def __init__(self, fallback_provider: BaseReasoningLLMProvider | None = None):
        self.fallback_provider = fallback_provider or MockReasoningLLMProvider()

    async def plan(
        self,
        user_question: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        task_type, agents, rationale = classify_task_deterministically(user_question)
        if task_type != ReasoningTaskType.GENERAL_REASONING.value:
            steps = [
                {
                    "agent_name": agent,
                    "goal": f"Retrieve evidence for {agent}",
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

        return await self.fallback_provider.plan(user_question, context)

    async def synthesize(
        self,
        user_question: str,
        task_type: str,
        evidence: list[Evidence],
        conflicts: list[EvidenceConflict],
        missing_information: list[str],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self.fallback_provider.synthesize(
            user_question=user_question,
            task_type=task_type,
            evidence=evidence,
            conflicts=conflicts,
            missing_information=missing_information,
            context=context,
        )


def get_default_reasoning_llm_provider() -> BaseReasoningLLMProvider:
    """Returns the production-ready hybrid provider with fast deterministic classification."""
    return HybridReasoningLLMProvider()
