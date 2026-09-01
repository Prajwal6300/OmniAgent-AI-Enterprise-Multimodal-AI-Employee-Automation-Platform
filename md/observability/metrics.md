# Observability — Prometheus Metrics & System Telemetry

## Status
**Status:** ✅ IMPLEMENTED (Prometheus Metrics Exporter)

---

## 1. Key Metrics Exposed (`/metrics`)

| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| **`http_requests_total`** | Counter | `method`, `endpoint`, `status_code` | Total HTTP requests handled by FastAPI. |
| **`http_request_duration_seconds`**| Histogram | `endpoint` | Request latency distributions. |
| **`agent_step_duration_seconds`** | Histogram | `agent_name`, `status` | Execution latency per specialized agent. |
| **`rag_vector_search_latency_seconds`**| Histogram | `tenant_id` | Cosine distance search latency in pgvector. |
| **`llm_token_usage_total`** | Counter | `model`, `type` (`prompt`/`completion`) | Total LLM tokens consumed. |
| **`active_workflow_runs`** | Gauge | `status` | Real-time count of active/suspended workflows. |
