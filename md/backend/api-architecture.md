# Backend — API Design & Communication Architecture

## Status
**Status:** ✅ IMPLEMENTED (RESTful v1 Endpoints & Server-Sent Events)

---

## 1. Communication Protocols

OmniAgent AI uses a hybrid communication architecture tailored for enterprise real-time responsiveness:

| Protocol | Transport | Endpoints | Use Case |
| :--- | :--- | :--- | :--- |
| **REST (JSON)** | HTTP/2 / HTTPS | `/api/v1/auth`, `/api/v1/documents`, `/api/v1/workflows` | Transactional CRUD operations, file metadata ingestion, workflow triggers. |
| **Server-Sent Events (SSE)** | HTTP Stream | `/api/v1/chat/sessions/{id}/stream` | Real-time streaming of LLM completion tokens, active agent step logs, and citations. |
| **WebSockets** | WS / WSS | `/api/v1/ws/notifications` | Real-time bi-directional push of urgent human approval modals and workflow state changes. |

---

## 2. Standardized JSON Envelope

All standard REST endpoints return consistent JSON envelopes:

### Success Response Format
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "timestamp": "2026-08-15T14:30:00Z",
    "request_id": "req_88129031",
    "execution_time_ms": 42.1
  }
}
```

### Error Response Format (RFC 7807)
```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "User does not have required role 'finance_manager' to approve invoice.",
    "details": { "required_role": "finance_manager", "current_role": "operator" },
    "request_id": "req_88129032"
  }
}
```
