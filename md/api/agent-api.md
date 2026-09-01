# API — Multi-Agent Execution & Trace Endpoints (`/api/v1/agents`)

## Status
**Status:** ✅ IMPLEMENTED (Direct Agent Invocations & Trace Waterfalls)

---

## 1. POST `/api/v1/agents/execute`
Directly invokes a specialized agent or the full LangGraph swarm for programmatic headless execution.

* **Method:** `POST`
* **Request:**
```json
{
  "target_agent": "supervisor",
  "task": "Reconcile attached invoice against database and check travel policy",
  "context": {
    "document_s3_key": "ten_001928/docs/inv_8812.pdf"
  }
}
```

* **Response (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "execution_id": "exec_991823",
    "final_state": "COMPLETED",
    "total_latency_ms": 2840,
    "agents_invoked": ["supervisor", "document_agent", "database_agent", "reasoning_agent"],
    "result": {
      "reconciliation_status": "MATCH_CONFIRMED",
      "variance": 0.00
    }
  }
}
```

---

## 2. GET `/api/v1/agents/traces/{execution_id}`
Fetches the granular step-by-step latency waterfall and agent scratchpad for telemetry inspection.

* **Method:** `GET`
* **Response (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "execution_id": "exec_991823",
    "steps": [
      { "agent": "supervisor", "duration_ms": 380, "tokens": 450 },
      { "agent": "document_agent", "duration_ms": 1120, "tokens": 1200 },
      { "agent": "database_agent", "duration_ms": 290, "tokens": 310 },
      { "agent": "reasoning_agent", "duration_ms": 1050, "tokens": 890 }
    ]
  }
}
```
