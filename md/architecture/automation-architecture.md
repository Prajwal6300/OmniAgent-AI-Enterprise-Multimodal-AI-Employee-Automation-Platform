# Architecture — Automation & Workflow Engine Architecture

## Status
**Status:** ✅ IMPLEMENTED (DAG Engine, Triggers, Approvals & Action Dispatcher)

---

## 1. Workflow Engine Architecture

OmniAgent AI features a stateful, event-driven **Workflow Automation Engine** capable of executing complex business processes spanning autonomous AI reasoning, deterministic conditional logic, human approval gates, and external API mutations.

```mermaid
flowchart TD
    subgraph Triggers [Event Trigger Layer]
        T_Man[Manual UI Trigger]
        T_Hook[Inbound Webhook]
        T_Cron[Scheduled Cron Job]
        T_File[S3 File Upload Ingestion]
        T_Mail[Incoming Email - IMAP]
    end

    subgraph Engine [Workflow DAG Execution Engine]
        Init[Parse Trigger Payload & Instantiate Run]
        Step_Exec[Execute Current DAG Step]
        Eval_Cond{Evaluate Step Conditions & Thresholds}
        Agent_Node[Invoke AI Agent Swarm]
        Risk_Eval{Evaluate Risk Tier: LOW / MED / HIGH}
    end

    subgraph HITL_Gate [Human-in-the-Loop Gateway]
        Suspend[Suspend Run & Save Checkpoint State]
        Notify_Approver[Dispatch Approval Request - UI / Slack]
        Human_Decision{Operator Decision}
        Resume[Resume DAG Execution]
        Abort[Abort Workflow & Record Audit Log]
    end

    subgraph Actions [Outbound Action Layer]
        Act_Exec[Execute Outbound Tool / API Mutation]
        Verify[Verify Action Success & Status Code]
        Complete[Record Completion Audit Record]
    end

    T_Man & T_Hook & T_Cron & T_File & T_Mail --> Init
    Init --> Step_Exec --> Eval_Cond
    Eval_Cond -->|Condition Met| Agent_Node
    Agent_Node --> Risk_Eval

    Risk_Eval -->|LOW Risk| Act_Exec
    Risk_Eval -->|MEDIUM / HIGH Risk| Suspend --> Notify_Approver --> Human_Decision
    Human_Decision -->|APPROVED| Resume --> Act_Exec
    Human_Decision -->|REJECTED| Abort

    Act_Exec --> Verify --> Complete
```

---

## 2. Core Automation Concepts

### 1. Workflow Definition (DAG Schema)
Workflows are defined as declarative JSON/YAML schemas composed of nodes (Triggers, Agent Tasks, Condition Gates, Approvals, and Tool Actions) connected by directional edges:
```json
{
  "workflow_id": "wf_invoice_proc_001",
  "name": "Automated Invoice 3-Way Match & ERP Post",
  "trigger": { "type": "file_upload", "folder": "invoices/" },
  "steps": [
    { "id": "extract_invoice", "type": "agent", "agent": "document_agent" },
    { "id": "fetch_po_gr", "type": "agent", "agent": "database_agent" },
    { "id": "match_items", "type": "agent", "agent": "reasoning_agent" },
    {
      "id": "approval_gate",
      "type": "human_approval",
      "condition": "amount > 5000.00 || match_variance > 0.01",
      "risk_level": "HIGH",
      "approver_roles": ["finance_manager", "admin"]
    },
    { "id": "post_erp", "type": "action", "action": "erp.post_invoice" }
  ]
}
```

### 2. Checkpointing & Fault Tolerance
* Every node execution state is stored in PostgreSQL and Redis.
* If a server restarts while a human approval is pending or an external API is experiencing transient downtime, the workflow resumes seamlessly from its exact suspension point with full execution context intact.
