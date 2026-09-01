# Observability — Multi-Agent Traces & Latency Waterfalls

## Status
**Status:** ✅ IMPLEMENTED (Granular Agent Execution Profiling)

---

## 1. Multi-Agent Latency Waterfall Visualization

For every complex user task or workflow execution, OmniAgent AI records a precise breakdown of time spent in each cognitive stage:

```text
========================================================================================
TASK EXECUTION TRACE #1042 — "Verify Invoice INV-8812 and Post to SAP"
========================================================================================
Stage / Agent                 Latency      Tokens    Status    Notes
----------------------------------------------------------------------------------------
1. Supervisor (Planning)      0.4s (380ms)   450      DONE      Intent: AP Reconciliation
2. Vision / Document Agent    1.8s (1820ms) 1,420     DONE      Extracted 12 Line Items
3. RAG Agent (Policy Check)   0.7s (690ms)   890      DONE      Cited Travel Policy p.14
4. Database Agent (SQL Query) 0.3s (280ms)   310      DONE      PO-9014 Found in DB
5. Reasoning Agent (3-Way)    2.1s (2100ms) 1,840     DONE      Variance: 0.00% (High Risk)
6. Action Agent (SAP Post)    0.5s (510ms)   120      DONE      SAP Doc #099412 Created
----------------------------------------------------------------------------------------
TOTAL EXECUTION TIME:         5.8s (5780ms) 5,030 Tokens  Result: SUCCESS
========================================================================================
```

---

## 2. Telemetry Persistence

This structured telemetry is stored in the `chat_messages.agent_steps` JSONB column and visualized directly within the Next.js chat interface.
