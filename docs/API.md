# OmniAgent AI — REST API & Orchestration Specification

All API endpoints are prefixed with `/api/v1` and return standardized JSON response envelopes.

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": { "request_id": "uuid", "timestamp": "ISO-8601" }
}
```

---

## 1. Authentication & Tenant Endpoints (`/api/v1/auth`)

### `POST /auth/login`
Authenticates user credentials and issues short-lived JWT access tokens and long-lived refresh tokens.
- **Request Body**:
  ```json
  { "email": "user@enterprise.com", "password": "secure_password" }
  ```
- **Response**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": { "id": "uuid", "email": "user@enterprise.com", "role": "Owner" }
  }
  ```

### `POST /auth/refresh`
Refreshes an expired access token using a valid refresh token.

### `POST /auth/logout`
Revokes active refresh tokens in the Redis token revocation registry.

---

## 2. Multi-Agent Orchestration & Chat (`/api/v1/orchestration`)

### `POST /orchestration/chat`
Dispatches conversational multi-agent turns through the LangGraph cognitive mesh.
- **Request Body**:
  ```json
  {
    "message": "Analyze Q3 financial report and flag any operational discrepancies.",
    "conversation_id": "uuid",
    "context": { "department": "Finance" },
    "attachments": [
      { "id": "doc_123", "type": "document", "url": "documents/q3.pdf" }
    ]
  }
  ```
- **Response**:
  ```json
  {
    "request_id": "uuid",
    "status": "COMPLETED",
    "answer": "The Q3 report shows a 12% increase in machine maintenance...",
    "citations": [
      { "chunk_id": "uuid", "document_name": "q3.pdf", "page": 4, "snippet": "..." }
    ],
    "steps_executed": ["supervisor", "document_agent", "reasoning_agent"],
    "requires_approval": false
  }
  ```

### `POST /orchestration/resume`
Resumes an orchestration flow paused pending human authorization.
- **Request Body**:
  ```json
  {
    "request_id": "uuid",
    "approval_id": "uuid",
    "decision": "APPROVED",
    "reason": "Verified and authorized by Supervisor"
  }
  ```

### `POST /orchestration/{request_id}/cancel`
Explicitly cancels an active or paused orchestration flow.

---

## 3. Knowledge & Documents (`/api/v1/documents`)

### `POST /documents/upload`
Uploads enterprise documents (PDF, DOCX, TXT) to tenant-scoped cloud object storage.
- **Form Data**: `file` (multipart/form-data)
- **Validation**: Magic bytes inspection, MIME verification, 25 MB max limit.

### `POST /documents/{id}/index`
Triggers chunking, semantic embedding generation, and vector indexing into `pgvector`.

---

## 4. Human-in-the-Loop Approvals (`/api/v1/approvals`)

### `GET /approvals/pending`
Lists all pending action requests requiring supervisor authorization.

### `POST /approvals/{id}/decide`
Submits an approval decision with cryptographic signature validation.
- **Request Body**:
  ```json
  { "decision": "APPROVED", "reason": "Operation verified safe" }
  ```

---

## 5. Automated Workflows (`/api/v1/workflows`)

### `POST /workflows`
Creates a declarative DAG workflow definition.

### `POST /workflows/{id}/run`
Triggers an immediate asynchronous execution of the workflow.

---

## 6. System Probes (`/api/v1/health`)

### `GET /health`
Liveness probe returning HTTP 200 and basic runtime metadata.

### `GET /ready`
Readiness probe verifying active connections to PostgreSQL, `pgvector` extension, Redis, and Supabase Object Storage.
