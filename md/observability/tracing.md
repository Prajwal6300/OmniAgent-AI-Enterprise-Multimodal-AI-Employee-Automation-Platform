# Observability — Distributed Tracing (OpenTelemetry)

## Status
**Status:** ✅ IMPLEMENTED (OpenTelemetry Instrumentation)

---

## 1. Distributed Tracing Topology

OmniAgent AI propagates `traceparent` context across FastAPI endpoints, LangGraph agent states, and asynchronous Celery tasks, allowing end-to-end trace visualization in Jaeger or OpenSearch.

```mermaid
flowchart LR
    A[Client Request: trace_id=4bf92f...] --> B[FastAPI Gateway Span]
    B --> C[Supervisor Planning Span]
    C --> D[Document Agent OCR Span]
    C --> E[Database Agent SQL Span]
    C --> F[Reasoning Agent Match Span]
    F --> G[Action Agent SAP Post Span]
```

Every database query, Redis checkpointer access, and external API call generates a correlated child span with execution timestamps and error flags.
