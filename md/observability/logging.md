# Observability — Structured Logging Architecture

## Status
**Status:** ✅ IMPLEMENTED (structlog JSON Formatter & Request Context)

---

## 1. Structured Logging Specification

OmniAgent AI utilizes `structlog` to emit machine-readable JSON log events to `stdout` containing distributed trace IDs, tenant context, and execution timing.

```json
{
  "timestamp": "2026-08-15T14:30:01.120Z",
  "level": "info",
  "logger": "app.agents.supervisor",
  "event": "SUPERVISOR_DECOMPOSED_PLAN",
  "request_id": "req_8819203910",
  "tenant_id": "ten_001928",
  "user_id": "usr_99120481",
  "session_id": "sess_881920-410a-42",
  "plan_task_count": 4,
  "execution_time_ms": 380.2
}
```

---

## 2. Log Levels & Retention

* **`DEBUG`**: Internal LLM token chunks, raw SQL queries, and OCR bounding box coordinates (disabled in production).
* **`INFO`**: Agent task dispatches, workflow state transitions, tool invocations, and HTTP request receipts.
* **`WARNING`**: LLM rate limits, tool retry attempts, and near-threshold memory consumption.
* **`ERROR`**: Caught exceptions, tool execution failures, and failed authentication attempts.
* **`CRITICAL`**: Database connection pool failure or unhandled fatal worker crashes.
