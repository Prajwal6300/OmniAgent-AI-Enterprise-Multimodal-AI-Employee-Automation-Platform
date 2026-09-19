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
    TaskType.ACTION_REQUEST.value: AgentTarget.ACTION_AGENT.value,
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
    TaskType.ACTION_REQUEST.value: "action_execution",
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

    # 2b. Ticket Action (e.g. "Create a maintenance ticket for machine M-102")
    ticket_pattern = r"\b(create|open|submit|raise)\b.*\b(ticket|maintenance request|work order)\b"
    if re.search(ticket_pattern, msg_lower) or "maintenance ticket" in msg_lower or "create ticket" in msg_lower:
        return SupervisorDecision(
            intent="create_ticket",
            task_type=TaskType.ACTION_REQUEST.value,
            capability=map_task_to_capability(TaskType.ACTION_REQUEST.value),
            selected_agent=AgentTarget.ACTION_AGENT.value,
            priority="medium",
            confidence=0.95,
            requires_tool=True,
            requires_approval=True,
            task_plan=[
                "Validate ticket parameters and machine identifier",
                "Require explicit human authorization for ticket submission",
                "Dispatch ticket creation to maintenance system",
                "Verify ticket ID persistence",
                "Record immutable audit log",
            ],
            explanation="Ticket creation request detected; routed to Action Agent requiring human approval.",
        )

    # 2c. Notification Action (e.g. "Notify the production team about this issue")
    notify_pattern = r"\b(notify|alert|broadcast)\b.*\b(team|production|manager|operator|user|staff)\b"
    if re.search(notify_pattern, msg_lower) or "send notification" in msg_lower:
        return SupervisorDecision(
            intent="send_notification",
            task_type=TaskType.ACTION_REQUEST.value,
            capability=map_task_to_capability(TaskType.ACTION_REQUEST.value),
            selected_agent=AgentTarget.ACTION_AGENT.value,
            priority="low",
            confidence=0.95,
            requires_tool=True,
            requires_approval=False,
            task_plan=[
                "Identify target recipient or operational group",
                "Construct notification payload with context",
                "Dispatch in-app notification via action service",
                "Confirm notification record creation",
                "Log action event",
            ],
            explanation="Notification dispatch request detected; routed to Action Agent.",
        )

    # 3. Multi-Source / Cross-Modal Reasoning / Trend / Root Cause (Reasoning Agent)
    has_img = any(k in msg_lower for k in ["image", "picture", "photo", "screenshot", "diagram", "inspection image"])
    has_db = any(k in msg_lower for k in [
        "maintenance record", "maintenance records", "maintenance history", "failures", "failure records",
        "failure record", "database", "orders", "production failures", "sales records"
    ])
    has_doc = any(k in msg_lower for k in ["manual", "handbook", "sop", "policy", "documentation", "invoice", "purchase order"])

    is_reasoning_task = (
        (has_img and has_db) or
        (has_doc and has_db) or
        ("troubleshooting procedure" in msg_lower and ("fail" in msg_lower or "manual" in msg_lower)) or
        ("troubleshooting step" in msg_lower and ("fail" in msg_lower or "manual" in msg_lower)) or
        re.search(r"\b(why might|most common causes|most likely reason|root cause)\b", msg_lower) or
        ("compare" in msg_lower and any(term in msg_lower for term in ["maintenance", "records", "history", "failures", "manual", "invoice with", "po"])) or
        ("production failures" in msg_lower and "summarize the most common causes" in msg_lower)
    )

    if is_reasoning_task and not (
        "delete" in msg_lower or
        "send this report" in msg_lower
    ):
        return SupervisorDecision(
            intent="multi_source_reasoning" if (has_img and has_db) else "analytical_reasoning",
            task_type=TaskType.DATA_ANALYSIS.value,
            capability=map_task_to_capability(TaskType.DATA_ANALYSIS.value),
            selected_agent=AgentTarget.REASONING_AGENT.value,
            priority="medium",
            confidence=0.96,
            requires_tool=False,
            requires_approval=False,
            task_plan=[
                "Identify required information sources and target specialist agents",
                "Dispatch coordinated queries to specialist agents",
                "Collect and normalize structured factual evidence",
                "Evaluate cross-source consistency and detect conflicts",
                "Synthesize grounded analytical conclusion without chain-of-thought exposure"
            ],
            explanation="Complex multi-source or multi-step analytical reasoning task routed to Reasoning Agent."
        )

    # 4. Document Analysis / PDF / Invoice / Contract / Policy / Manual / Report
    doc_keywords = [
        "pdf", "invoice", "document", "docx", "contract", "receipt",
        "purchase order", "po-", "agreement", "manual", "machine manual", "report"
    ]
    doc_verbs = [
        "summarize", "analyze", "parse", "extract", "verify",
        "read", "scan", "compare", "explain", "findings"
    ]

    # Specific real-world company document tasks
    img_terms = ["image", "picture", "photo", "screenshot", "diagram", "defect", "blueprint"]
    is_doc_task = (
        (any(k in msg_lower for k in doc_keywords) and any(v in msg_lower for v in doc_verbs)) or
        msg_lower.startswith(("summarize this", "read this invoice", "parse this")) or
        "findings from this report" in msg_lower or
        "safety instructions in this machine manual" in msg_lower or
        "read this invoice" in msg_lower or
        "summarize this invoice" in msg_lower or
        "summarize this company leave policy" in msg_lower or
        "explain the important safety instructions" in msg_lower
    )

    if is_doc_task and not (
        "database" in msg_lower or
        "delete" in msg_lower or
        "send this report" in msg_lower or
        any(it in msg_lower for it in img_terms)
    ):
        intent_type = "document_processing"
        if "invoice" in msg_lower:
            intent_type = "invoice_extraction"
        elif "policy" in msg_lower:
            intent_type = "policy_summarization"
        elif "manual" in msg_lower:
            intent_type = "technical_manual_analysis"
        elif "report" in msg_lower:
            intent_type = "report_analysis"
        elif "pdf" in msg_lower:
            intent_type = "pdf_analysis"

        return SupervisorDecision(
            intent=intent_type,
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
                "Identify key fields, sections, or line items",
                "Synthesize findings and return verified structured result"
            ],
            explanation="Request involves document parsing, extraction, or summarization routed to Document Agent."
        )

    # 4. Image Analysis / Machine Visual / Screenshot / Inspection
    img_keywords = [
        "image", "picture", "photo", "screenshot", "diagram", "defect",
        "machine image", "blueprint", "visual inspection", "machine inspection",
        "visible damage", "damaged components", "serial number from this",
        "extract the serial number", "objects are visible", "components are visible",
        "components are present", "safety issues visible", "visible condition"
    ]
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
    db_keywords = [
        "database", "sql", "sales amount", "query table", "select from", "db query", "total revenue from database",
        "production failure", "production failures", "failed inspection", "failed inspections", "open maintenance request",
        "pending orders", "pending order", "orders are pending", "top 10 products", "products by usage",
        "machines had the most failures", "machines by failures", "top 5 machines by failures",
        "purchase amount by vendor", "average production time", "how many pending orders"
    ]
    if any(k in msg_lower for k in db_keywords):
        return SupervisorDecision(
            intent="database_query",
            task_type=TaskType.DATABASE_QUERY.value,
            capability=map_task_to_capability(TaskType.DATABASE_QUERY.value),
            selected_agent=AgentTarget.DATABASE_AGENT.value,
            priority="medium",
            confidence=0.96,
            requires_tool=False,
            requires_approval=False,
            task_plan=[
                "Analyze natural language question against authorized business schema",
                "Construct parameterized read-only SQL query plan",
                "Validate query against SQL safety guardrails and tenant isolation",
                "Execute read-only query and synthesize grounded summary"
            ],
            explanation="Structured database metric query detected; routed to Database Agent."
        )

    # 6. Knowledge Search / Policies / Handbook / Guidelines / Agreements / Procedures
    rag_keywords = [
        "policy", "leave policy", "handbook", "guideline", "procedure", "knowledge base",
        "vacation rules", "hr policy", "password policy", "vendor agreement", "payment term",
        "safety requirements", "machine fails", "sop", "standard operating procedure"
    ]
    if any(k in msg_lower for k in rag_keywords):
        return SupervisorDecision(
            intent="knowledge_search",
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
