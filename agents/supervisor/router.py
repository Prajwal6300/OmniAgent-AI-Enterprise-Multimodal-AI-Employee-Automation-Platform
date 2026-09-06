import re

from agents.supervisor.schemas import AgentTarget, SupervisorDecision, TaskType

# Capability and Task Type to Agent Mapping
TASK_TYPE_TO_AGENT: dict[str, str] = {
    TaskType.DOCUMENT_ANALYSIS.value: AgentTarget.DOCUMENT_AGENT.value,
    TaskType.IMAGE_ANALYSIS.value: AgentTarget.VISION_AGENT.value,
    TaskType.KNOWLEDGE_SEARCH.value: AgentTarget.RAG_AGENT.value,
    TaskType.DATABASE_QUERY.value: AgentTarget.DATABASE_AGENT.value,
    TaskType.DATA_ANALYSIS.value: AgentTarget.REASONING_AGENT.value,
    TaskType.REPORT_GENERATION.value: AgentTarget.REASONING_AGENT.value,
    TaskType.EMAIL.value: AgentTarget.ACTION_AGENT.value,
    TaskType.WORKFLOW.value: AgentTarget.ACTION_AGENT.value,
    TaskType.AUTOMATION.value: AgentTarget.ACTION_AGENT.value,
    TaskType.GENERAL_QUERY.value: AgentTarget.SUPERVISOR.value,
    TaskType.UNKNOWN.value: AgentTarget.SUPERVISOR.value,
}

TASK_TYPE_TO_CAPABILITY: dict[str, str] = {
    TaskType.DOCUMENT_ANALYSIS.value: "document_analysis",
    TaskType.IMAGE_ANALYSIS.value: "image_analysis",
    TaskType.KNOWLEDGE_SEARCH.value: "knowledge_search",
    TaskType.DATABASE_QUERY.value: "database_query",
    TaskType.DATA_ANALYSIS.value: "data_analysis",
    TaskType.REPORT_GENERATION.value: "report_generation",
    TaskType.EMAIL.value: "email_communication",
    TaskType.WORKFLOW.value: "workflow_orchestration",
    TaskType.AUTOMATION.value: "task_automation",
    TaskType.GENERAL_QUERY.value: "general_assistance",
    TaskType.UNKNOWN.value: "unknown",
}


def map_task_to_agent(task_type: str) -> str:
    """Maps a task type to its corresponding agent logical name."""
    return TASK_TYPE_TO_AGENT.get(task_type.upper(), AgentTarget.SUPERVISOR.value)


def map_task_to_capability(task_type: str) -> str:
    """Maps a task type to its normalized capability identifier."""
    return TASK_TYPE_TO_CAPABILITY.get(task_type.upper(), "unknown")


def create_fallback_decision(explanation: str | None = None, error: str | None = None) -> SupervisorDecision:
    """Produces a safe, deterministic fallback decision adhering to strict specifications."""
    default_exp = explanation or "The request could not be confidently classified."
    if error:
        default_exp = f"{default_exp} (Reason: {error})"
    return SupervisorDecision(
        intent="unknown",
        task_type=TaskType.UNKNOWN.value,
        capability="unknown",
        selected_agent=AgentTarget.SUPERVISOR.value,
        priority="medium",
        confidence=0.0,
        requires_tool=False,
        requires_approval=False,
        task_plan=[],
        explanation=default_exp,
    )


def deterministic_classify(message: str) -> SupervisorDecision | None:
    """
    High-performance, deterministic pattern classifier.
    Handles obvious enterprise requests instantly without LLM latency,
    and supports 100% offline, deterministic testing.
    """
    msg_clean = message.strip()
    msg_lower = msg_clean.lower()

    if not msg_clean:
        return None

    # 1. High-risk / Destructive Actions (Delete, Deletion, Drop, Terminate, Wipe, Purge)
    destructive_actions = r"(delete|deletion|drop|remove|removal|purge|wipe|destroy|destruction|terminate|termination|truncate)"
    destructive_targets = r"(record|employee|user|table|database|account|file|data)"
    destructive_regex_1 = rf"\b{destructive_actions}\b.*\b{destructive_targets}\b"
    destructive_regex_2 = rf"\b{destructive_targets}\b.*\b{destructive_actions}\b"

    if (
        re.search(destructive_regex_1, msg_lower) or
        re.search(destructive_regex_2, msg_lower) or
        "database deletion" in msg_lower or
        "delete the employee record" in msg_lower or
        "delete this employee record" in msg_lower or
        "purge_all_records" in msg_lower
    ):
        return SupervisorDecision(
            intent="destructive_data_action",
            task_type=TaskType.AUTOMATION.value,
            capability=map_task_to_capability(TaskType.AUTOMATION.value),
            selected_agent=AgentTarget.ACTION_AGENT.value,
            priority="high",
            confidence=0.96,
            requires_tool=True,
            requires_approval=True,
            task_plan=[
                "Verify enterprise identity and deletion credentials",
                "Require explicit human-in-the-loop approval token",
                "Stage safe audit log entry with entry hash",
                "Execute deletion upon verified approval",
                "Log action into immutable audit records"
            ],
            explanation="Destructive operation detected; elevated to high priority requiring mandatory human approval."
        )

    # 2. Email / Send / Dispatch Action (e.g. "Send this report to the manager")
    send_pattern = r"\b(send|email|mail|dispatch|forward)\b.*\b(report|manager|team|finance|customer|email|message)\b"
    if re.search(send_pattern, msg_lower) or "send this report" in msg_lower:
        return SupervisorDecision(
            intent="dispatch_report",
            task_type=TaskType.REPORT_GENERATION.value,
            capability=map_task_to_capability(TaskType.REPORT_GENERATION.value),
            selected_agent=AgentTarget.ACTION_AGENT.value,
            priority="medium",
            confidence=0.95,
            requires_tool=True,
            requires_approval=False,
            task_plan=[
                "Retrieve generated report contents",
                "Identify target recipient email address",
                "Format executive summary and attachments",
                "Dispatch email via action service tool",
                "Confirm delivery status"
            ],
            explanation="Request requires report compilation and external dispatch tool execution."
        )

    # 3. Document Analysis / PDF / Invoice / Contract
    doc_keywords = ["pdf", "invoice", "document", "docx", "contract", "receipt", "purchase order", "po-", "agreement"]
    doc_verbs = ["summarize", "analyze", "parse", "extract", "verify", "read", "scan", "compare"]
    if any(k in msg_lower for k in doc_keywords) and any(v in msg_lower for v in doc_verbs):
        return SupervisorDecision(
            intent="document_processing",
            task_type=TaskType.DOCUMENT_ANALYSIS.value,
            capability=map_task_to_capability(TaskType.DOCUMENT_ANALYSIS.value),
            selected_agent=AgentTarget.DOCUMENT_AGENT.value,
            priority="medium",
            confidence=0.96,
            requires_tool=False,
            requires_approval=False,
            task_plan=[
                "Ingest and validate document structure",
                "Extract structured text, tables, and metadata",
                "Identify key fields and line items",
                "Synthesize findings and return summary"
            ],
            explanation="Request involves document parsing and text extraction routed to Document Agent."
        )
    if msg_lower.startswith(("summarize this pdf", "analyze this invoice")):
        return SupervisorDecision(
            intent="document_summarization",
            task_type=TaskType.DOCUMENT_ANALYSIS.value,
            capability=map_task_to_capability(TaskType.DOCUMENT_ANALYSIS.value),
            selected_agent=AgentTarget.DOCUMENT_AGENT.value,
            priority="medium",
            confidence=0.98,
            requires_tool=False,
            requires_approval=False,
            task_plan=[
                "Load PDF content",
                "Extract high-fidelity sections",
                "Generate executive summary"
            ],
            explanation="PDF analysis detected; routed to Document Agent."
        )

    # 4. Image Analysis / Machine Visual / Screenshot / Inspection
    img_keywords = ["image", "picture", "photo", "screenshot", "diagram", "defect", "machine image", "blueprint"]
    if any(k in msg_lower for k in img_keywords):
        return SupervisorDecision(
            intent="visual_inspection",
            task_type=TaskType.IMAGE_ANALYSIS.value,
            capability=map_task_to_capability(TaskType.IMAGE_ANALYSIS.value),
            selected_agent=AgentTarget.VISION_AGENT.value,
            priority="medium",
            confidence=0.95,
            requires_tool=False,
            requires_approval=False,
            task_plan=[
                "Acquire image artifact",
                "Apply visual feature extraction and object detection",
                "Identify defects, annotations, or components",
                "Synthesize visual analysis report"
            ],
            explanation="Visual inspection request detected; routed to Vision Agent."
        )

    # 5. Database Query / SQL / Aggregations (Read-only queries)
    db_keywords = ["database", "sql", "sales amount", "query table", "select from", "db query", "total revenue from database"]
    if any(k in msg_lower for k in db_keywords):
        return SupervisorDecision(
            intent="database_aggregation",
            task_type=TaskType.DATABASE_QUERY.value,
            capability=map_task_to_capability(TaskType.DATABASE_QUERY.value),
            selected_agent=AgentTarget.DATABASE_AGENT.value,
            priority="medium",
            confidence=0.96,
            requires_tool=False,
            requires_approval=False,
            task_plan=[
                "Translate inquiry into read-only SQL query",
                "Validate query against SQL safety guardrails",
                "Execute read-only database query",
                "Format aggregated results"
            ],
            explanation="Structured database metric query detected; routed to Database Agent."
        )

    # 6. Knowledge Search / Policies / Handbook / Guidelines
    rag_keywords = ["policy", "leave policy", "handbook", "guideline", "procedure", "knowledge base", "vacation rules", "hr policy"]
    if any(k in msg_lower for k in rag_keywords):
        return SupervisorDecision(
            intent="policy_search",
            task_type=TaskType.KNOWLEDGE_SEARCH.value,
            capability=map_task_to_capability(TaskType.KNOWLEDGE_SEARCH.value),
            selected_agent=AgentTarget.RAG_AGENT.value,
            priority="low",
            confidence=0.94,
            requires_tool=False,
            requires_approval=False,
            task_plan=[
                "Embed query for semantic similarity search",
                "Retrieve top-k relevant policy clauses from vector store",
                "Re-rank retrieved passages for precision",
                "Synthesize verified policy answer with citations"
            ],
            explanation="Enterprise knowledge inquiry detected; routed to RAG Agent."
        )

    # 7. General Greetings / Platform Capabilities
    general_patterns = [r"^(hi|hello|hey|greetings|who are you|what can you do|help)\b"]
    if any(re.search(p, msg_lower) for p in general_patterns):
        return SupervisorDecision(
            intent="general_greeting",
            task_type=TaskType.GENERAL_QUERY.value,
            capability=map_task_to_capability(TaskType.GENERAL_QUERY.value),
            selected_agent=AgentTarget.SUPERVISOR.value,
            priority="low",
            confidence=0.90,
            requires_tool=False,
            requires_approval=False,
            task_plan=["Acknowledge greeting", "Explain platform capabilities"],
            explanation="General inquiry routed to Supervisor for direct response."
        )

    # 8. Unclassified, Ambiguous, or Gibberish Requests -> Safe UNKNOWN Fallback
    return create_fallback_decision(explanation="The request could not be confidently classified.")
