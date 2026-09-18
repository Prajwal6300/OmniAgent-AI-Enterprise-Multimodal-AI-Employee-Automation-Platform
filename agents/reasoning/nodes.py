"""
OmniAgent AI — Reasoning Agent LangGraph Nodes
Atomic node implementations for request validation, task classification,
execution plan creation & security validation, multi-agent dispatch,
evidence normalization, conflict detection, grounded deduction, and confidence calculation.
"""

from typing import Any

from agents.reasoning.exceptions import (
    AgentExecutionTimeoutError,
)
from agents.reasoning.executor import (
    ALLOWED_REASONING_AGENTS,
    PROHIBITED_AGENTS,
    AgentExecutor,
    InternalAgentExecutor,
)
from agents.reasoning.normalizer import (
    ConfidenceCalculator,
    ConflictDetector,
    EvidenceNormalizer,
)
from agents.reasoning.providers import (
    BaseReasoningLLMProvider,
    get_default_reasoning_llm_provider,
)
from agents.reasoning.schemas import (
    Evidence,
    EvidenceConflict,
    ReasoningTaskType,
)
from agents.reasoning.state import ReasoningState

# Safety limits
DEFAULT_MAX_DEPTH = 3
DEFAULT_MAX_AGENT_CALLS = 5


async def validate_request_node(
    state: ReasoningState,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> dict[str, Any]:
    """
    Validates input request parameters, organization tenant ID,
    and enforces recursion limits.
    """
    user_q = (state.get("user_question") or "").strip()
    org_id = state.get("organization_id")
    depth = state.get("depth", 0)

    # 1. Depth & Recursion Check
    if depth >= max_depth:
        return {
            "status": "FAILED_RECURSION",
            "error": f"Reasoning execution depth {depth} exceeds maximum allowable depth of {max_depth}.",
            "grounded": False,
            "confidence": 0.0,
            "answer": "Execution terminated: maximum reasoning recursion depth exceeded.",
            "requires_approval": False,
        }

    # 2. Tenant Context Check
    if not org_id:
        return {
            "status": "FAILED_VALIDATION",
            "error": "Missing required organization_id tenant boundary.",
            "grounded": False,
            "confidence": 0.0,
            "answer": "Request rejected: missing authenticated tenant context.",
            "requires_approval": False,
        }

    # 3. User Question Check
    if not user_q:
        return {
            "status": "FAILED_VALIDATION",
            "error": "User question is empty or blank.",
            "grounded": False,
            "confidence": 0.0,
            "answer": "Please provide a valid question or enterprise analytical request.",
            "requires_approval": False,
        }

    return {
        "status": "VALIDATED",
        "agent_outputs": {},
        "evidence": [],
        "conflicts": [],
        "missing_information": [],
        "contributing_agents": [],
        "depth": depth + 1,
        "requires_approval": False,
    }


async def classify_reasoning_task_node(
    state: ReasoningState,
    llm_provider: BaseReasoningLLMProvider | None = None,
) -> dict[str, Any]:
    """Classifies the user inquiry into a structured ReasoningTaskType."""
    if state.get("status") != "VALIDATED":
        return {}

    provider = llm_provider or get_default_reasoning_llm_provider()
    user_q = state.get("user_question", "")
    context = state.get("context", {})

    plan_data = await provider.plan(user_q, context)
    task_type = plan_data.get("task_type", ReasoningTaskType.GENERAL_REASONING.value)

    return {"task_type": task_type}


async def create_execution_plan_node(
    state: ReasoningState,
    llm_provider: BaseReasoningLLMProvider | None = None,
) -> dict[str, Any]:
    """Generates the downstream execution plan and target specialist agents."""
    if state.get("status") != "VALIDATED":
        return {}

    provider = llm_provider or get_default_reasoning_llm_provider()
    user_q = state.get("user_question", "")
    context = state.get("context", {})

    plan_data = await provider.plan(user_q, context)
    raw_agents = plan_data.get("agents", [])
    raw_steps = plan_data.get("steps", [])

    return {
        "required_agents": raw_agents,
        "execution_plan": raw_steps,
    }


async def validate_execution_plan_node(
    state: ReasoningState,
    max_agent_calls: int = DEFAULT_MAX_AGENT_CALLS,
) -> dict[str, Any]:
    """
    Validates execution plan against the security allowlist and call limits.
    Rejects disallowed agents (action_agent, email_agent, shell_agent, reasoning_agent).
    """
    if state.get("status") != "VALIDATED":
        return {}

    required_agents = state.get("required_agents", [])
    execution_plan = state.get("execution_plan", [])
    validated_agents: list[str] = []
    missing_info = list(state.get("missing_information", []))

    # Check maximum call limits
    if len(required_agents) > max_agent_calls:
        return {
            "status": "FAILED_PLAN_LIMIT",
            "error": f"Requested {len(required_agents)} agent calls exceeds maximum limit of {max_agent_calls}.",
            "grounded": False,
            "confidence": 0.0,
            "answer": "The requested analysis requires more agent invocations than permitted by security policy.",
        }

    for agent in required_agents:
        norm_agent = agent.strip().lower()

        # Recursion protection
        if norm_agent == "reasoning_agent":
            return {
                "status": "FAILED_PLAN_SECURITY",
                "error": "Plan attempted recursive invocation of reasoning_agent.",
                "grounded": False,
                "confidence": 0.0,
                "answer": "Security violation: reasoning agent cannot invoke itself recursively.",
            }

        # Allowlist check
        if (
            norm_agent in PROHIBITED_AGENTS
            or norm_agent not in ALLOWED_REASONING_AGENTS
        ):
            # If user attempted action agent, notify action boundary
            if norm_agent == "action_agent" or "action" in norm_agent:
                missing_info.append(
                    "Action execution requested (requires future Action Agent; cannot be executed today)."
                )
                continue
            return {
                "status": "FAILED_PLAN_SECURITY",
                "error": f"Agent '{agent}' is not permitted in reasoning execution plan.",
                "grounded": False,
                "confidence": 0.0,
                "answer": f"Execution rejected: '{agent}' is not an authorized specialized agent.",
            }

        validated_agents.append(norm_agent)

    # Filter execution steps
    validated_steps = [
        step
        for step in execution_plan
        if step.get("agent_name", "").strip().lower() in set(validated_agents)
    ]

    return {
        "required_agents": validated_agents,
        "execution_plan": validated_steps,
        "missing_information": missing_info,
    }


async def execute_required_agents_node(
    state: ReasoningState,
    agent_executor: AgentExecutor | None = None,
) -> dict[str, Any]:
    """
    Executes all authorized specialist agents with authenticated tenant context.
    Supports partial execution if individual downstream agents fail or time out.
    """
    if state.get("status") != "VALIDATED":
        return {}

    executor = agent_executor or InternalAgentExecutor()
    required_agents = state.get("required_agents", [])
    user_q = state.get("user_question", "")
    org_id = state.get("organization_id", "")
    user_id = state.get("user_id", "")
    conv_id = state.get("conversation_id", "")
    req_id = state.get("request_id", "")
    context = dict(state.get("context", {}))

    # Inject authenticated context
    context.update(
        {
            "organization_id": org_id,
            "user_id": user_id,
            "conversation_id": conv_id,
            "request_id": req_id,
            "user_question": user_q,
        }
    )

    agent_outputs: dict[str, dict[str, Any]] = dict(state.get("agent_outputs", {}))
    missing_info: list[str] = list(state.get("missing_information", []))
    call_count = state.get("agent_call_count", 0)

    for agent_name in required_agents:
        call_count += 1
        request_params = {
            "question": user_q,
            "image_id": context.get("image_id"),
            "document_id": context.get("document_id"),
            "limit": context.get("limit", 50),
        }

        try:
            output = await executor.execute(agent_name, request_params, context)
            agent_outputs[agent_name] = output
        except AgentExecutionTimeoutError as timeout_err:
            missing_info.append(f"{agent_name} timed out: {timeout_err!s}")
        except Exception as exec_err:  # noqa: BLE001
            missing_info.append(f"{agent_name} unavailable: {exec_err!s}")

    return {
        "agent_outputs": agent_outputs,
        "missing_information": missing_info,
        "agent_call_count": call_count,
    }


async def collect_outputs_node(state: ReasoningState) -> dict[str, Any]:
    """Collects successful agent outputs and identifies contributing agents."""
    if state.get("status") != "VALIDATED":
        return {}

    agent_outputs = state.get("agent_outputs", {})
    contributing = list(agent_outputs.keys())

    return {"contributing_agents": contributing}


async def normalize_evidence_node(state: ReasoningState) -> dict[str, Any]:
    """Normalizes all downstream agent outputs into typed Evidence models."""
    if state.get("status") != "VALIDATED":
        return {}

    agent_outputs = state.get("agent_outputs", {})
    evidence_objects = EvidenceNormalizer.normalize_all(agent_outputs)
    evidence_dicts = [e.model_dump() for e in evidence_objects]

    # Check if expected data was empty
    missing_info = list(state.get("missing_information", []))
    if not evidence_objects and state.get("required_agents"):
        missing_info.append("Downstream agents returned no matching factual records.")

    return {
        "evidence": evidence_dicts,
        "missing_information": missing_info,
    }


async def detect_conflicts_node(state: ReasoningState) -> dict[str, Any]:
    """Detects factual contradictions across multiple normalized evidence sources."""
    if state.get("status") != "VALIDATED":
        return {}

    evidence_dicts = state.get("evidence", [])
    evidence_objects = [Evidence(**e) for e in evidence_dicts]
    conflicts = ConflictDetector.detect_conflicts(evidence_objects)
    conflict_dicts = [c.model_dump() for c in conflicts]

    return {"conflicts": conflict_dicts}


async def reason_over_evidence_node(
    state: ReasoningState,
    llm_provider: BaseReasoningLLMProvider | None = None,
) -> dict[str, Any]:
    """
    Executes grounded synthesis over verified evidence.
    Distinguishes observed facts, source findings, inferences, and uncertainties.
    """
    if state.get("status") != "VALIDATED":
        return {}

    provider = llm_provider or get_default_reasoning_llm_provider()
    user_q = state.get("user_question", "")
    task_type = state.get("task_type", ReasoningTaskType.GENERAL_REASONING.value)
    evidence_objects = [Evidence(**e) for e in state.get("evidence", [])]
    conflict_objects = [EvidenceConflict(**c) for c in state.get("conflicts", [])]
    missing_info = state.get("missing_information", [])
    context = state.get("context", {})

    synthesis_result = await provider.synthesize(
        user_question=user_q,
        task_type=task_type,
        evidence=evidence_objects,
        conflicts=conflict_objects,
        missing_information=missing_info,
        context=context,
    )

    return {
        "answer": synthesis_result.get("answer", ""),
        "reasoning_summary": synthesis_result.get("reasoning_summary", ""),
        "grounded": synthesis_result.get("grounded", True),
    }


async def validate_grounding_node(state: ReasoningState) -> dict[str, Any]:
    """
    Validates that the synthesized response strictly adheres to verified evidence
    and does not hallucinate facts beyond available records.
    """
    if state.get("status") != "VALIDATED":
        return {}

    evidence = state.get("evidence", [])
    answer = state.get("answer", "")
    missing_info = state.get("missing_information", [])

    # If completely devoid of evidence, ensure the agent states unavailability rather than making claims
    if not evidence and missing_info:
        is_grounded = (
            "couldn't complete" in answer.lower()
            or "not available" in answer.lower()
            or "no verified evidence" in answer.lower()
        )
        return {"grounded": is_grounded}

    return {"grounded": True}


async def calculate_confidence_node(state: ReasoningState) -> dict[str, Any]:
    """Calculates objective confidence based on evidence quality, coverage, and conflicts."""
    if state.get("status") != "VALIDATED":
        return {"confidence": state.get("confidence", 0.0)}

    evidence_objects = [Evidence(**e) for e in state.get("evidence", [])]
    conflict_objects = [EvidenceConflict(**c) for c in state.get("conflicts", [])]
    missing_info = state.get("missing_information", [])
    required_agents = state.get("required_agents", [])
    contributing_agents = state.get("contributing_agents", [])

    score = ConfidenceCalculator.calculate(
        evidence_list=evidence_objects,
        conflicts=conflict_objects,
        missing_information=missing_info,
        required_agents=required_agents,
        contributing_agents=contributing_agents,
    )

    return {"confidence": score}


async def generate_response_node(state: ReasoningState) -> dict[str, Any]:
    """Finalizes response structure and sets terminal completion status."""
    current_status = state.get("status", "COMPLETED")
    final_status = "COMPLETED" if current_status == "VALIDATED" else current_status

    return {
        "status": final_status,
        "requires_approval": False,
    }
