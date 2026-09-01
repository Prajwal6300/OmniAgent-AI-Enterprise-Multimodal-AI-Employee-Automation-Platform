# Automation — Workflow Engine Architecture & Execution

## Status
**Status:** ✅ IMPLEMENTED (DAG Workflow Engine with Redis/PostgreSQL State)

---

## 1. Workflow Engine Overview

The OmniAgent AI **Workflow Engine** is a distributed, stateful orchestrator that executes enterprise business processes modeled as Directed Acyclic Graphs (DAGs). It coordinates asynchronous agent reasoning steps, deterministic condition checks, human approval gates, and outbound tool actions.

```mermaid
flowchart TD
    A[Event Ingested: Webhook / Upload / Cron] --> B[Workflow Trigger Matcher]
    B --> C[Instantiate WorkflowRun Record in DB]
    
    C --> D[Load Workflow DAG Definition]
    
    D --> E[Execute Node 1: Ingestion / Agent]
    E --> F[Persist Step State to Redis & PostgreSQL]
    
    F --> G{Next Node Type}
    
    G -->|Condition Branch| H[Evaluate Expression]
    G -->|Agent Task| I[Invoke LangGraph Agent]
    G -->|Human Approval| J[Suspend Run & Dispatch Approval]
    G -->|Action Mutation| K[Execute Outbound Tool Call]
    
    H --> F
    I --> F
    J --> L{Wait for Operator Approval}
    L -->|Approved| F
    L -->|Rejected| M[Halt Workflow & Log Audit Event]
    K --> F
    
    F --> N{Are all DAG nodes complete?}
    N -->|No| G
    N -->|Yes| O[Mark WorkflowRun as COMPLETED & Send Summary]
```

---

## 2. Technical Capabilities

| Capability | Specification | Implementation Detail |
| :--- | :--- | :--- |
| **State Persistence** | PostgreSQL + Redis Checkpoints | Every DAG node transition writes execution logs and scratchpads atomically. |
| **Concurrency** | Celery Distributed Workers | Concurrent multi-tenant workflow execution across distributed task queues. |
| **Idempotency** | UUID Idempotency Keys | Guarantees that retrying a failed workflow step does not double-post ERP invoices or resend duplicate emails. |
| **Suspension & Resume** | LangGraph Memory Checkpointer | Workflows can stay paused for days waiting for human approval without consuming active server threads. |
| **Timeout & SLA** | Configurable Step Timeouts | Steps exceeding execution limits (e.g., 30s for LLM inference) trigger retry or fallback branches. |
