# Portfolio — 20-Question Enterprise Technical Interview Guide

---

## 1. What is OmniAgent AI?
OmniAgent AI is a production-grade multimodal autonomous AI employee and enterprise workflow platform. It ingests complex multimodal business artifacts—including scanned PDFs, machine photos, voice memos, Excel sheets, and SQL tables—and autonomously decomposes, reasons, approves, executes, and audits cross-department enterprise workflows.

---

## 2. Why did you build it?
Modern enterprise operations spend up to 40% of their working hours manually gathering, cross-referencing, and re-keying data between unstructured documents and ERP systems. Existing RPA scripts are too brittle to handle variations, while standard conversational chatbots lack database execution, deterministic tool safety, human approval guardrails, and compliance auditability. OmniAgent AI was built to deliver a reliable, grounded, and safe digital employee for enterprise workflows.

---

## 3. Why Multimodal AI?
Over 80% of actionable enterprise data exists outside plain text—in scanned PDF invoices, machine defect photos, executive voicemails, and complex spreadsheets. Multimodal alignment allows the system to extract, reason across, and verify data directly in its native representation without fragile third-party translation pipelines.

---

## 4. Why Multi-Agent Architecture?
Single monolithic LLM prompts fail on long-horizon complex tasks due to context pollution, prompt drift, and an inability to compartmentalize permissions. Breaking the system into specialized agents (Supervisor, Vision, Document, RAG, Database, Reasoning, Action) provides modular reasoning, dedicated tool scopes, deterministic debugging, and isolated security boundaries.

---

## 5. Why LangGraph?
Unlike unconstrained multi-agent loops (AutoGPT / CrewAI) that can wander or loop indefinitely, LangGraph models agent workflows as stateful, Directed Acyclic Graphs (DAGs) and state machines. It natively supports state checkpointing (in Redis and PostgreSQL), cyclical retries with self-correction, and asynchronous human approval interruptions.

---

## 6. Why PostgreSQL + pgvector instead of a standalone vector database?
PostgreSQL 16 with `pgvector` consolidates relational transactional data (users, workflows, approvals, audit logs) and high-dimensional vector embeddings in a single ACID-compliant database engine. This eliminates the operational complexity, network latency, and synchronization lag of maintaining external vector databases like Pinecone or Milvus, while supporting transactional joins between relational business records and vector similarity scores.

---

## 7. How does the Supervisor Agent work?
The Supervisor acts as the master orchestrator. It receives the user prompt and multimodal artifacts, executes intent classification and task planning, decomposes the request into atomic sub-tasks, and delegates work to specialized worker agents. It tracks graph state transitions, aggregates worker outputs, and formats the final verified response.

---

## 8. How does Deterministic Tool Calling work?
Tools are defined as typed Python functions decorated with Pydantic v2 schemas. When an agent emits a JSON tool invocation, Pydantic strictly validates parameter types and boundary constraints. If validation fails, an auto-healing feedback loop returns the schema error to the LLM for immediate correction. Approved tool calls execute within sandboxed environments with mandatory timeout constraints.

---

## 9. How do you prevent Hallucinations?
1. **Hybrid RAG Grounding:** Queries are resolved against dense vector indexes (pgvector) and sparse BM25 full-text indexes, reranked by Cross-Encoder.
2. **Two-Pass Grounding Verification:** An internal verification evaluator decomposes the generated text into atomic assertions and verifies that each claim is supported by retrieved citations.
3. **Deterministic Arithmetic:** Mathematical totals, taxes, and variances are calculated using Python Decimal rather than LLM text generation.
4. **Explicit Refusal:** If evidence is absent, the model explicitly responds with structured refusal rather than guessing.

---

## 10. How do you prevent Prompt Injection?
1. **Delimiter Sandboxing:** All untrusted external documents, emails, and user inputs are strictly framed inside dedicated delimiter tokens (`<<<UNTRUSTED_CONTENT>>>`) and treated as passive data.
2. **Scope-Bound Tool Execution:** Agents cannot invoke tools based on document instructions; tool invocations are strictly matched against active user RBAC session permissions.
3. **Structured Outputs:** Forcing model responses into Pydantic JSON schemas structurally invalidates free-form adversarial injection scripts.

---

## 11. How do you secure database queries?
The Database Agent operates under **strictly read-only PostgreSQL credentials**. Synthesized SQL queries are passed through an Abstract Syntax Tree (AST) validator that blocks all DDL (`DROP`, `ALTER`, `CREATE`) and DML mutations (`INSERT`, `UPDATE`, `DELETE`), enforcing mandatory `LIMIT` constraints on every query.

---

## 12. How does the Human-in-the-Loop (HITL) approval system work?
Actions are classified into three risk tiers:
* **LOW RISK:** Read-only queries, logging, status cards -> Auto-executed.
* **MEDIUM RISK:** Reversible external communications -> Review or auto-pass.
* **HIGH RISK:** Financial disbursements, ERP ledger mutations, machinery commands -> **Workflow suspended**.
When suspended, the LangGraph checkpointer serializes execution state to PostgreSQL/Redis. The workflow remains paused until an authorized human manager authorizes the action via the Next.js approval portal with an HMAC digital signature.

---

## 13. How does the Automation Engine work?
The automation engine executes declarative JSON/YAML workflow DAGs triggered by file uploads to S3, incoming webhooks, scheduled cron jobs, or manual user requests. It coordinates agent nodes, evaluates conditional branching expressions, pauses at human approval gates, and dispatches outbound tool actions with full state persistence and retry handling.

---

## 14. How does the system scale horizontally?
* **Stateless API & UI:** The FastAPI backend and Next.js frontend are stateless containers scaled horizontally behind an Nginx / ALB reverse proxy.
* **Distributed Task Workers:** Heavy OCR, Whisper transcription, and chunking jobs run asynchronously on distributed Celery worker pools backed by Redis message queues.
* **Database Optimization:** PostgreSQL connection pooling is handled via `asyncpg` with HNSW vector indexing providing sub-50ms retrieval over millions of embeddings.

---

## 15. What happens if a sub-agent fails?
If a sub-agent encounters an error (e.g., an invalid SQL column or ambiguous table layout), the traceback and diagnostic hints are returned to the Supervisor. The Supervisor re-routes the task with corrected instructions (up to 3 retries). If still unresolved, it halts the branch safely and reports the specific failure reason to the user.

---

## 16. What happens if an external LLM provider is down?
The dynamic Model Gateway features automated circuit breakers and failovers. If Anthropic Claude 3.5 Sonnet experiences 5 consecutive rate-limit or 5xx errors within 60 seconds, the circuit trips and immediately diverts traffic to OpenAI GPT-4o or local self-hosted Ollama instances.

---

## 17. How do you evaluate RAG quality?
We run continuous evaluation using the **Ragas** framework on a golden enterprise test dataset, benchmarking:
* **Faithfulness / Groundedness** ($\ge 0.95$)
* **Answer Relevancy** ($\ge 0.90$)
* **Context Precision** ($\ge 0.88$)
* **Context Recall** ($\ge 0.90$)

---

## 18. How do you monitor agent performance and cost?
1. **OpenTelemetry Tracing:** Distributed spans track latency across every supervisor decision, sub-agent invocation, and tool call.
2. **Prometheus Metrics:** Tracks request throughput, error rates, and P95 latency distributions.
3. **Token & Cost Attribution:** Captures prompt and completion tokens per model and computes real-time USD costs per tenant/department against allocated monthly budgets.

---

## 19. How do you guarantee audit compliance?
Every critical mutation, approval decision, and workflow run generates an entry in the `audit_logs` table. Each row includes the `tenant_id`, `user_id`, `timestamp`, `action_payload`, and an **HMAC SHA-256 digital signature** generated using a vault secret key, providing non-repudiation and cryptographic proof against retroactive log tampering.

---

## 20. What would you improve or build next?
1. **Multi-Agent Cross-Organization Negotiation:** Enabling secure agent-to-agent negotiations between buyers and suppliers.
2. **LoRA Adapters:** Training custom low-rank adaptation models on domain-specific engineering schematics.
3. **Native SAP RFC Binary Adapters:** Direct binary RFC protocol support for on-premise SAP ECC installations.
