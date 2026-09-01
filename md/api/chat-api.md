# API — Conversational & Streaming Chat Endpoints (`/api/v1/chat`)

## Status
**Status:** ✅ IMPLEMENTED (REST Sessions & Server-Sent Events Streaming)

---

## 1. POST `/api/v1/chat/sessions`
Initializes a new conversational session.

* **Method:** `POST`
* **Request:** `{ "title": "Invoice Audit Review" }`
* **Response (`201 Created`):**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_881920-410a-42",
    "created_at": "2026-08-15T14:30:00Z"
  }
}
```

---

## 2. GET `/api/v1/chat/sessions/{id}/stream`
Streams multi-agent reasoning steps, token completions, citations, and tool events via Server-Sent Events (SSE).

* **Method:** `GET`
* **Parameters:** `prompt` (string), `s3_keys` (optional array of S3 string URIs).
* **Response Content-Type:** `text/event-stream`

### Wire Event Stream Output Example
```text
event: agent_step
data: {"agent": "document_agent", "status": "EXTRACTING_TABLES", "latency_ms": 320}

event: token
data: {"content": "I have extracted "}

event: token
data: {"content": "invoice INV-2026-8812. Total is $14,250.00."}

event: citation
data: {"doc_id": "doc_9918", "source": "Invoice_8812.pdf", "page": 1}

event: done
data: {"status": "SUCCESS", "session_id": "sess_881920-410a-42"}
```
