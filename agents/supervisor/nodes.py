import time
from typing import Any

from agents.supervisor.exceptions import LLMProviderError
from agents.supervisor.prompts import SUPERVISOR_SYSTEM_PROMPT
from agents.supervisor.providers import BaseLLMProvider, get_default_llm_provider
from agents.supervisor.router import (
    create_fallback_decision,
    map_task_to_agent,
    map_task_to_capability,
)
from agents.supervisor.schemas import AgentTarget, SupervisorDecision, TaskType
from agents.supervisor.state import SupervisorState


async def validate_request_node(state: SupervisorState) -> dict[str, Any]:
    """
    Validates that:
    1. user_message exists and is non-empty.
    2. message length is within acceptable boundaries (<= 10,000 characters).
    3. Identifiers and context format are valid.
    """
    raw_message = state.get("user_message")
    
    if raw_message is None or not isinstance(raw_message, str):
        return {
            "status": "FAILED_VALIDATION",
            "error": "Empty or missing user request message.",
            "confidence": 0.0,
            "task_type": TaskType.UNKNOWN.value,
            "selected_agent": AgentTarget.SUPERVISOR.value,
            "explanation": "Validation failed: Request message is required."
        }

    stripped_msg = raw_message.strip()
    if len(stripped_msg) == 0:
        return {
            "status": "FAILED_VALIDATION",
            "error": "User message cannot be empty or whitespace only.",
            "confidence": 0.0,
            "task_type": TaskType.UNKNOWN.value,
            "selected_agent": AgentTarget.SUPERVISOR.value,
            "explanation": "Validation failed: Message cannot be empty."
        }

    # Security check: Extremely large inputs (buffer protection)
    MAX_ALLOWED_LEN = 10000
    if len(stripped_msg) > MAX_ALLOWED_LEN:
        return {
            "status": "FAILED_VALIDATION",
            "error": f"Message length exceeds maximum allowable threshold ({MAX_ALLOWED_LEN} characters).",
            "confidence": 0.0,
            "task_type": TaskType.UNKNOWN.value,
            "selected_agent": AgentTarget.SUPERVISOR.value,
            "explanation": "Validation failed: Request payload exceeded character limit."
        }

    return {
        "status": "VALIDATED",
        "user_message": stripped_msg,
        "error": None
    }


async def classify_intent_node(
    state: SupervisorState,
    provider: BaseLLMProvider = None
) -> dict[str, Any]:
    """
    Classifies the user's intent and high-level task type.
    Uses LLM abstraction or deterministic fast-path.
    """
    if state.get("status") == "FAILED_VALIDATION":
        return {}

    user_message = state.get("user_message", "")
    llm_provider = provider or get_default_llm_provider()

    t_start = time.time()
    try:
        raw_res = await llm_provider.generate_decision_json(
            user_message=user_message,
            system_prompt=SUPERVISOR_SYSTEM_PROMPT,
            context=state.get("context", {})
        )
        llm_latency_ms = round((time.time() - t_start) * 1000, 2)

        # Strict validation of provider output
        if not isinstance(raw_res, dict) or ("intent" not in raw_res and "task_type" not in raw_res):
            raise LLMProviderError("Malformed LLM response: missing required classification attributes.")

        # Extract intent and task type
        raw_task_type = str(raw_res.get("task_type", TaskType.UNKNOWN.value)).upper()
        if raw_task_type not in [t.value for t in TaskType]:
            raw_task_type = TaskType.UNKNOWN.value

        raw_intent = str(raw_res.get("intent", "unspecified_intent")).lower().replace(" ", "_")
        
        # If task type is unknown, confidence must be 0.0
        if raw_task_type == TaskType.UNKNOWN.value:
            conf = 0.0
        else:
            conf = float(raw_res.get("confidence", 0.90))
        clamped_conf = max(0.0, min(1.0, conf))

        selected_agent = raw_res.get("selected_agent")

        return {
            "intent": raw_intent,
            "task_type": raw_task_type,
            "selected_agent": selected_agent,
            "confidence": clamped_conf,
            "explanation": raw_res.get("explanation", ""),
            "task_plan": raw_res.get("task_plan", []),
            "priority": raw_res.get("priority", "medium"),
            "requires_tool": bool(raw_res.get("requires_tool", False)),
            "requires_approval": bool(raw_res.get("requires_approval", False)),
            "llm_latency_ms": llm_latency_ms,
            "status": "CLASSIFIED"
        }
    except Exception as exc:  # noqa: BLE001
        llm_latency_ms = round((time.time() - t_start) * 1000, 2)
        return {
            "status": "CLASSIFICATION_ERROR",
            "error": f"LLM classification error: {exc!s}",
            "task_type": TaskType.UNKNOWN.value,
            "selected_agent": AgentTarget.SUPERVISOR.value,
            "intent": "unknown",
            "confidence": 0.0,
            "llm_latency_ms": llm_latency_ms,
            "explanation": "Failed to classify user request due to upstream provider error."
        }


async def determine_capability_node(state: SupervisorState) -> dict[str, Any]:
    """
    Translates task_type into a canonical system capability identifier.
    """
    if state.get("status") in ["FAILED_VALIDATION", "CLASSIFICATION_ERROR"]:
        return {"capability": "unknown"}

    task_type = state.get("task_type", TaskType.UNKNOWN.value)
    capability = map_task_to_capability(task_type)
    return {
        "capability": capability
    }


async def select_agent_node(state: SupervisorState) -> dict[str, Any]:
    """
    Maps capability / task_type to target specialized agent logical name.
    Preserves explicitly chosen agent if already assigned by classifier.
    """
    if state.get("status") in ["FAILED_VALIDATION", "CLASSIFICATION_ERROR"]:
        return {"selected_agent": AgentTarget.SUPERVISOR.value}

    # If already selected by classifier / router rule
    existing_agent = state.get("selected_agent")
    if existing_agent and existing_agent in [a.value for a in AgentTarget]:
        return {"selected_agent": existing_agent}

    task_type = state.get("task_type", TaskType.UNKNOWN.value)
    target_agent = map_task_to_agent(task_type)
    return {
        "selected_agent": target_agent
    }


async def determine_risk_node(state: SupervisorState) -> dict[str, Any]:
    """
    Evaluates execution risk, human-in-the-loop approval requirement,
    and external tool requirements.
    Enforces that destructive or state-mutating actions require approval.
    """
    if state.get("status") in ["FAILED_VALIDATION", "CLASSIFICATION_ERROR"]:
        return {
            "priority": "medium",
            "requires_tool": False,
            "requires_approval": False
        }

    user_msg = state.get("user_message", "").lower()
    task_type = state.get("task_type", TaskType.UNKNOWN.value)
    selected_agent = state.get("selected_agent", AgentTarget.SUPERVISOR.value)
    
    # Existing flags from classifier
    requires_tool = state.get("requires_tool", False)
    requires_approval = state.get("requires_approval", False)
    priority = state.get("priority", "medium")

    # Guardrails: Hard security overrides for destructive actions
    destructive_keywords = ["delete", "drop table", "truncate", "purge", "destroy", "wipe", "terminate account"]
    if any(k in user_msg for k in destructive_keywords):
        priority = "high"
        requires_approval = True
        requires_tool = True

    # Actions involving email or workflow or action agent require tools
    if task_type in [TaskType.EMAIL.value, TaskType.WORKFLOW.value, TaskType.AUTOMATION.value] or selected_agent == AgentTarget.ACTION_AGENT.value:
        requires_tool = True

    # Read-only inquiries never require approval
    if task_type in [TaskType.DOCUMENT_ANALYSIS.value, TaskType.IMAGE_ANALYSIS.value, TaskType.KNOWLEDGE_SEARCH.value, TaskType.GENERAL_QUERY.value]:
        requires_approval = False

    return {
        "priority": priority,
        "requires_tool": requires_tool,
        "requires_approval": requires_approval
    }


async def create_task_plan_node(state: SupervisorState) -> dict[str, Any]:
    """
    Generates or ensures a concise operational task plan without chain-of-thought.
    """
    if state.get("status") in ["FAILED_VALIDATION", "CLASSIFICATION_ERROR"] or state.get("task_type") == TaskType.UNKNOWN.value:
        return {"task_plan": []}

    existing_plan = state.get("task_plan")
    if existing_plan and isinstance(existing_plan, list) and len(existing_plan) > 0:
        # Sanitize plan: limit to 6 concise steps
        sanitized_plan = [str(step)[:150] for step in existing_plan[:6]]
        return {"task_plan": sanitized_plan}

    # Generate standard template operational plan according to task type
    task_type = state.get("task_type", TaskType.UNKNOWN.value)
    plans: dict[str, list[str]] = {
        TaskType.DOCUMENT_ANALYSIS.value: [
            "Ingest uploaded document artifact",
            "Extract structured text and key fields",
            "Synthesize verified document findings"
        ],
        TaskType.IMAGE_ANALYSIS.value: [
            "Load visual image artifact",
            "Perform feature detection and visual inspection",
            "Synthesize inspection findings"
        ],
        TaskType.KNOWLEDGE_SEARCH.value: [
            "Retrieve relevant documentation from knowledge base",
            "Extract and rank supporting evidence passages",
            "Synthesize grounded answer with source citations"
        ],
        TaskType.DATABASE_QUERY.value: [
            "Translate request into safe read-only SQL query",
            "Validate query guardrails",
            "Execute query and format structured result set"
        ],
        TaskType.DATA_ANALYSIS.value: [
            "Gather numeric data points",
            "Execute variance and reconciliation computations",
            "Synthesize analytical summary"
        ],
        TaskType.REPORT_GENERATION.value: [
            "Aggregate multi-source input metrics",
            "Format comprehensive report sections",
            "Prepare final executive brief"
        ],
        TaskType.EMAIL.value: [
            "Draft email body and subject line",
            "Verify recipient routing",
            "Queue email dispatch tool"
        ],
        TaskType.WORKFLOW.value: [
            "Verify workflow preconditions",
            "Execute step sequence via integration connectors",
            "Audit workflow completion state"
        ],
        TaskType.AUTOMATION.value: [
            "Verify user authorizations and human approval gates",
            "Execute automated task sequence",
            "Record execution audit log"
        ],
        TaskType.GENERAL_QUERY.value: [
            "Understand user query",
            "Synthesize direct response"
        ],
        TaskType.UNKNOWN.value: []
    }

    return {"task_plan": plans.get(task_type, [])}


async def validate_decision_node(state: SupervisorState) -> dict[str, Any]:
    """
    Final validator ensuring all output fields adhere to strict enterprise schemas.
    Applies fail-safe fallback if any constraint is violated.
    """
    status = state.get("status", "SUCCESS")
    error = state.get("error")

    if status in ["FAILED_VALIDATION", "CLASSIFICATION_ERROR"] or error is not None:
        fallback = create_fallback_decision(
            explanation=state.get("explanation"),
            error=error
        )
        return {
            "intent": fallback.intent,
            "task_type": fallback.task_type,
            "capability": fallback.capability,
            "selected_agent": fallback.selected_agent,
            "priority": fallback.priority,
            "confidence": 0.0,
            "requires_tool": fallback.requires_tool,
            "requires_approval": fallback.requires_approval,
            "task_plan": fallback.task_plan,
            "explanation": fallback.explanation,
            "status": "COMPLETED_FALLBACK"
        }

    # Validate output bounds
    try:
        task_type = state.get("task_type", TaskType.UNKNOWN.value)
        if task_type == TaskType.UNKNOWN.value:
            conf = 0.0
        else:
            conf = float(state.get("confidence", 0.0))
            conf = max(0.0, min(1.0, conf))

        priority = state.get("priority", "medium")
        if priority not in ["low", "medium", "high"]:
            priority = "medium"

        decision = SupervisorDecision(
            intent=state.get("intent", "unknown"),
            task_type=task_type,
            capability=state.get("capability", "unknown"),
            selected_agent=state.get("selected_agent", AgentTarget.SUPERVISOR.value),
            priority=priority,
            confidence=conf,
            requires_tool=state.get("requires_tool", False),
            requires_approval=state.get("requires_approval", False),
            task_plan=state.get("task_plan", []),
            explanation=state.get("explanation", "")
        )

        return {
            "intent": decision.intent,
            "task_type": decision.task_type,
            "capability": decision.capability,
            "selected_agent": decision.selected_agent,
            "priority": decision.priority,
            "confidence": decision.confidence,
            "requires_tool": decision.requires_tool,
            "requires_approval": decision.requires_approval,
            "task_plan": decision.task_plan,
            "explanation": decision.explanation,
            "status": "COMPLETED"
        }
    except Exception as exc:  # noqa: BLE001
        fallback = create_fallback_decision(
            explanation="Decision schema validation failed.",
            error=str(exc)
        )
        return {
            "intent": fallback.intent,
            "task_type": fallback.task_type,
            "capability": fallback.capability,
            "selected_agent": fallback.selected_agent,
            "priority": fallback.priority,
            "confidence": 0.0,
            "requires_tool": fallback.requires_tool,
            "requires_approval": fallback.requires_approval,
            "task_plan": fallback.task_plan,
            "explanation": fallback.explanation,
            "status": "COMPLETED_FALLBACK",
            "error": str(exc)
        }
