# Frontend — API Integration & Streaming Protocols

## Status
**Status:** ✅ IMPLEMENTED (Axios Interceptors, SSE Stream Consumer & WebSocket Client)

---

## 1. Client-Side API Architecture

The frontend communicates with the FastAPI gateway via a centralized Axios instance configured with JWT refresh interceptors, SSE streaming readers, and WebSocket listeners.

```mermaid
flowchart TD
    A[React Component] --> B[Axios API Client / SSE Reader]
    
    B --> C{Request Interceptor: Attach JWT Bearer}
    C --> D[FastAPI Backend: /api/v1/*]
    
    D --> E{Response Status}
    E -->|200 OK| F[Return Data to React Query Cache]
    E -->|401 Token Expired| G[Axios Response Interceptor: POST /api/v1/auth/refresh]
    
    G -->|Refresh Succeeded| H[Re-dispatch Original Request with New JWT]
    G -->|Refresh Failed| I[Redirect to /login & Purge State]
```

---

## 2. Server-Sent Events (SSE) Wire Protocol

Streaming endpoints emit structured JSON events:
```text
event: step_start
data: {"agent": "supervisor", "task": "Decomposing goals", "timestamp": "2026-08-15T14:30:01Z"}

event: token
data: {"content": "Based "}

event: token
data: {"content": "on the verified "}

event: token
data: {"content": "invoice..."}

event: citation
data: {"source": "Invoice_8812.pdf", "page": 1, "score": 0.99}

event: done
data: {"status": "SUCCESS", "total_duration_ms": 1420}
```
