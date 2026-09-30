"""
OmniAgent AI Documentation - Part 4 (Sections 66 to 95)
"""

def get_part4() -> str:
    return r'''# 66. Troubleshooting

This section details common operational issues, diagnostic steps, and resolutions:

### 1. Backend Does Not Start
- **Symptom**: `uvicorn` fails immediately upon execution.
- **Cause**: Unbound port 8000, missing Python virtual environment, or missing mandatory dependencies.
- **Check**: Run `netstat -ano | findstr :8000` (Windows) or `lsof -i :8000` (Linux).
- **Fix**: Terminate the conflicting process or run uvicorn on an alternate port (`--port 8001`). Ensure `pip install -r backend/requirements.txt` succeeded.

### 2. Frontend Cannot Connect to Backend
- **Symptom**: Network error or `ERR_CONNECTION_REFUSED` in browser console.
- **Cause**: Backend is not running or `VITE_API_BASE_URL` is misconfigured.
- **Check**: Test `curl http://localhost:8000/api/v1/health`.
- **Fix**: Set `VITE_API_BASE_URL=http://localhost:8000/api/v1` in `frontend/.env` or rely on Nginx reverse proxy.

### 3. CORS Error in Browser
- **Symptom**: `Access to fetch at ... has been blocked by CORS policy`.
- **Cause**: Client origin (e.g. `http://localhost:5173`) is not in `ALLOWED_ORIGINS`.
- **Check**: Inspect `ALLOWED_ORIGINS` in `.env`.
- **Fix**: Update `.env` to include your client URL: `ALLOWED_ORIGINS="http://localhost:5173,http://localhost:3000"`.

### 4. Database Connection Failure
- **Symptom**: `asyncpg.exceptions.CannotConnectNowError` or connection timeout.
- **Cause**: PostgreSQL container is offline, credentials in `DATABASE_URL` are incorrect, or port 5432 is unreachable.
- **Check**: Run `docker compose ps postgres` and inspect logs via `docker compose logs postgres`.
- **Fix**: Start the container with `docker compose up -d postgres`. Verify `DATABASE_URL` format.

### 5. Alembic Migration Failure
- **Symptom**: `alembic.util.exc.CommandError: Can't locate revision identified by '...'`.
- **Cause**: Database migration state is out of sync with migration scripts in `backend/migrations/versions/`.
- **Check**: Run `alembic current` and inspect the `alembic_version` table in PostgreSQL.
- **Fix**: Run `alembic stamp head` if models are already synchronized, or rollback conflicting revisions.

### 6. pgvector Unavailable
- **Symptom**: `type "vector" does not exist` during table creation or migration.
- **Cause**: Database image lacks the pgvector extension or `CREATE EXTENSION IF NOT EXISTS vector;` was not run.
- **Check**: Connect via `psql` and execute `SELECT * FROM pg_extension WHERE extname = 'vector';`.
- **Fix**: Ensure you are using `pgvector/pgvector:pg16` in Docker Compose and run `CREATE EXTENSION IF NOT EXISTS vector;`.

### 7. Embedding Generation Failure
- **Symptom**: `openai.RateLimitError` or `AuthenticationError` during document ingestion.
- **Cause**: Missing or expired `OPENAI_API_KEY`.
- **Check**: Inspect `backend/app/core/config.py` settings or test key directly via curl.
- **Fix**: Provide a valid API key in `.env` or set `EMBEDDING_PROVIDER=deterministic` for mock/local offline testing.

### 8. LLM API Call Failure
- **Symptom**: `AgentExecutionFailedError` or 500 error on chat endpoint.
- **Cause**: Upstream LLM provider outage or rate-limiting.
- **Check**: Inspect `execution_events` or structlog error entries for upstream status codes.
- **Fix**: Retry request, verify credit balance with LLM provider, or configure automated retries.

### 9. RAG Returns No Results
- **Symptom**: RAG query returns `"I cannot find sufficient verifiable information..."`.
- **Cause**: Document chunks not indexed, query similarity falls below `RAG_SIMILARITY_THRESHOLD (0.05)`, or tenant isolation filtered chunks.
- **Check**: Verify chunk count in database: `SELECT count(*) FROM document_chunks WHERE organization_id = :org_id;`.
- **Fix**: Upload and trigger indexing on the document via `POST /api/v1/documents/{id}/index`. Lower similarity threshold if necessary.

### 10. File Upload Failure
- **Symptom**: `400 Bad Request: File exceeds maximum allowed size` or unsupported extension.
- **Cause**: File size > 25MB or extension not in `[.pdf, .docx, .txt]`.
- **Check**: Check file size on disk and verify MIME header in HTTP request.
- **Fix**: Compress the document or convert to a supported format.

### 11. Docker Networking Issue
- **Symptom**: `backend` container cannot resolve `postgres` or `redis`.
- **Cause**: Services are running on disconnected Docker networks or containers crashed.
- **Check**: Run `docker network inspect omniagent-network`.
- **Fix**: Restart the stack with `docker compose down && docker compose up -d`.

### 12. Nginx Proxy Issue
- **Symptom**: `502 Bad Gateway` returned by Nginx on `/api/v1/*`.
- **Cause**: Backend container is not healthy or upstream hostname `backend:8000` is unreachable.
- **Check**: Run `docker compose logs frontend` and `docker compose logs backend`.
- **Fix**: Ensure `backend` container is healthy before routing Nginx traffic.

### 13. Environment Variable Missing
- **Symptom**: `RuntimeError: DATABASE_URL environment variable must be set`.
- **Cause**: `.env` file not copied from `.env.example` or required variable omitted.
- **Check**: Run `python -c "from app.core.config import settings; print(settings.DATABASE_URL)"`.
- **Fix**: Populate `.env` with required variables and restart the server.

### 14. Authentication Failure
- **Symptom**: `401 Unauthorized: Could not validate credentials`.
- **Cause**: Missing `Authorization: Bearer <TOKEN>` header or expired JWT token.
- **Check**: Inspect `localStorage.getItem("token")` in browser developer tools.
- **Fix**: Re-authenticate via `POST /api/v1/auth/login` to obtain a fresh access token.

### 15. JWT Token Tampering
- **Symptom**: `401 Unauthorized: Signature verification failed`.
- **Cause**: Client token was signed with an older or different `JWT_SECRET`.
- **Check**: Verify if `JWT_SECRET` changed in `.env`.
- **Fix**: Clear browser localStorage and log in again.

### 16. Agent Routing Failure
- **Symptom**: Supervisor routes instruction to `NONE` or unexpected specialist.
- **Cause**: Ambiguous user prompt or prompt injection pattern triggered safety fallback.
- **Check**: Inspect `intent` and `task_type` in `SupervisorAnalyzeData` response.
- **Fix**: Rephrase prompt clearly, providing explicit instructions or file attachments.

### 17. Action Approval Failure
- **Symptom**: `400 Bad Request: Approval has expired or payload hash mismatch`.
- **Cause**: 30-minute approval window elapsed, or input parameters were modified after approval generation.
- **Check**: Check `expires_at` and `payload_hash` in `action_approvals` table.
- **Fix**: Generate a new approval request and approve within 30 minutes.

### 18. Workflow Run Stalled
- **Symptom**: Workflow run status remains `PENDING` or `WAITING_FOR_APPROVAL`.
- **Cause**: Workflow execution was suspended pending human authorization.
- **Check**: Query `GET /api/v1/workflow-runs/{run_id}`.
- **Fix**: Submit an approval decision via `POST /api/v1/workflow-runs/{run_id}/resume`.

---

# 67. Common Errors

| Error Code | HTTP Status | Root Cause | Immediate Resolution |
| :--- | :---: | :--- | :--- |
| `ValidationError` | 400 | Missing required fields or invalid types | Check request JSON against Pydantic schema |
| `AuthenticationError` | 401 | Missing, malformed, or expired Bearer JWT | Re-login via `/api/v1/auth/login` |
| `AuthorizationError` | 403 | User role lacks required capability | Request role elevation from Organization Admin |
| `NotFoundError` | 404 | Resource does not exist or belongs to another tenant | Verify UUID and authenticated tenant scope |
| `TenantSecurityViolation` | 403 | Attempted access across organizational boundary | Ensure authenticated user owns requested resource |
| `PromptInjectionDetected` | 400 | Adversarial instruction override detected | Rephrase instruction without override tokens |
| `MaxStepsExceededError` | 400 | LangGraph execution exceeded 20 steps | Decompose complex composite query into steps |
| `ExecutionTimeoutError` | 504 | Operation exceeded 120-second timeout | Optimize query or run task asynchronously |

---

# 68. Development Workflow

1. **Branch Creation**: Create a branch off `develop`: `git checkout -b feature/your-feature-name`.
2. **Local Environment**: Activate virtual environment and ensure Docker infrastructure services are up.
3. **Database Changes**: If modifying SQLAlchemy models in `backend/app/models/`, generate a migration:
   ```bash
   cd backend
   alembic revision --autogenerate -m "describe_model_change"
   alembic upgrade head
   ```
4. **Code Quality Verification**:
   ```bash
   ruff check backend agents automation multimodal tools tests
   ruff format backend agents automation multimodal tools tests
   cd frontend && npm run lint
   ```
5. **Execute Test Suite**: Ensure all unit and integration tests pass:
   ```bash
   pytest tests/ -v
   ```

---

# 69. Git Workflow

- **Branching Model**: GitFlow-inspired branching strategy (`main` for production releases, `develop` for active integration, `feature/*` for new capabilities, `fix/*` for bug fixes).
- **Commit Messages**: Follow Conventional Commits specification:
  - `feat(agents)`: Add new capability to Action Agent
  - `fix(rag)`: Correct cosine distance query binding
  - `docs(api)`: Update endpoint reference table
  - `test(security)`: Add prompt injection regression tests

---

# 70. Code Standards

- **Python**: Complies with PEP 8 and enforced via **Ruff**. Python 3.11 type hints (`str | None`, `list[dict]`) required on all functions.
- **FastAPI / Pydantic**: Pydantic v2 conventions (`model_dump()`, `model_validate()`, `Field(...)`).
- **SQLAlchemy**: Async 2.0 syntax (`select(Model).where(...)`, `await session.execute(...)`).
- **TypeScript**: Strict mode enabled (`tsconfig.json`). No untyped `any` in production services.
- **React**: Functional components with hooks, typed props, and Tailwind utility styling.

---

# 71. Security Checklist

| Item | Verification Target | Implemented Status | Verification Evidence |
| :---: | :--- | :---: | :--- |
| 1 | Passwords hashed with bcrypt (salt generated per user) | ✅ Implemented | `backend/app/core/security.py` |
| 2 | JWT access tokens expire in 60 minutes | ✅ Implemented | `backend/app/core/config.py` |
| 3 | Refresh tokens expire in 7 days | ✅ Implemented | `backend/app/core/config.py` |
| 4 | Row-level tenant isolation on all database models | ✅ Implemented | `organization_id` foreign key on 27 models |
| 5 | Read-only enforcement on Text-to-SQL queries | ✅ Implemented | `agents/database/security.py` |
| 6 | SQL system catalog probing prohibited | ✅ Implemented | `agents/database/security.py` |
| 7 | Mandatory tenant filtering on all SQL statements | ✅ Implemented | `agents/database/security.py` |
| 8 | Adversarial prompt injection regex scanning | ✅ Implemented | `agents/vision/security.py` |
| 9 | Untrusted document/image data isolated in delimiters | ✅ Implemented | `agents/vision/security.py` |
| 10 | Path traversal checks on storage file paths | ✅ Implemented | `agents/vision/security.py` |
| 11 | Uploaded file size restricted (25MB doc / 10MB image) | ✅ Implemented | `backend/app/services/document_service.py` |
| 12 | Filename sanitization on upload | ✅ Implemented | `agents/vision/security.py` |
| 13 | HMAC-SHA256 signature verification on approvals | ✅ Implemented | `agents/action/approval.py` |
| 14 | SHA-256 payload hashing binding approval to input | ✅ Implemented | `agents/action/approval.py` |
| 15 | Action approval expiration enforcement (30 mins) | ✅ Implemented | `agents/action/approval.py` |
| 16 | SHA-256 hash chaining of audit log entries | ✅ Implemented | `backend/app/services/audit_service.py` |
| 17 | Tool permission checking against user roles | ✅ Implemented | `tools/common/permissions.py` |
| 18 | Suppression of private chain-of-thought tokens | ✅ Implemented | `agents/reasoning/agent.py` |
| 19 | CORS origins restricted via configuration | ✅ Implemented | `backend/app/main.py` |
| 20 | Request ID tracing on all incoming HTTP requests | ✅ Implemented | `backend/app/core/middleware.py` |

---

# 72. Feature Matrix

| Feature Domain | Feature Name | Status | Notes |
| :--- | :--- | :---: | :--- |
| **Authentication** | User Registration & Login | ✅ Implemented | JWT HS256 tokens, bcrypt password hashing |
| **Authentication** | Refresh Token Rotation | ✅ Implemented | 7-day refresh token expiration |
| **Authorization** | Role-Based Access Control (RBAC) | ✅ Implemented | 6 system roles, granular permissions |
| **Multi-Tenancy** | Organization Isolation | ✅ Implemented | Enforced across relational DB, RAG, and storage |
| **Document AI** | PDF, DOCX, TXT Parsing | ✅ Implemented | Structured extraction, layout parsing |
| **RAG** | Vector Semantic Retrieval | ✅ Implemented | PostgreSQL 16 `pgvector`, 1536-dim embeddings |
| **RAG** | Verifiable Source Citations | ✅ Implemented | Attached to answers with page and section info |
| **RAG** | Cross-Encoder Reranking | 🟡 Partially Implemented | Top_k pass-through active in current release |
| **Database AI** | Text-to-SQL Conversion | ✅ Implemented | Natural language to read-only SQL |
| **Database AI** | Zero-Trust SQL Guardrails | ✅ Implemented | Blocks DDL, DML, and system catalogs |
| **Computer Vision** | Image Validation & Sizing | ✅ Implemented | Max 4096x4096px, 10MB limit |
| **Computer Vision** | Optical Character Recognition (OCR) | ✅ Implemented | System engine wrapper (Tesseract) |
| **Computer Vision** | Object & Defect Detection | ✅ Implemented | YOLO/OpenCV wrapper with honest fallback |
| **Multimodal** | Audio Processing & Transcription | 🟡 Partially Implemented | Mock/Scaffolding provider active |
| **Multimodal** | Video Keyframe & Event Extraction | 🟡 Partially Implemented | Mock/Scaffolding provider active |
| **Reasoning** | Cross-Modal Evidence Reconciliation | ✅ Implemented | Multi-source conflict detection |
| **Actuation** | Enterprise Action Execution | ✅ Implemented | Email, tickets, reports, notifications |
| **Governance** | Human-in-the-Loop Approvals | ✅ Implemented | HMAC-SHA256 signing, payload hash binding |
| **Automation** | Multi-Step Workflow Engine | ✅ Implemented | StepExecutor, state recovery, cancel/resume |
| **Auditing** | Cryptographic Audit Trail | ✅ Implemented | SHA-256 hash chaining of all system events |

---

# 73. Agent Capability Matrix

| Agent Name | Primary Purpose | Input Modalities | Primary Output | Tools & Integrations | Database Access | Approval Gate? | Status |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **Supervisor** | Intent classification & DAG planning | Text, Attachments | Decision & Plan DAG | None (Internal) | No | No | ✅ Implemented |
| **Document** | Parsing, classification, extraction | PDF, DOCX, TXT | Structured fields, tables | Local / MinIO | Read-Only | No | ✅ Implemented |
| **RAG** | Semantic vector knowledge search | Text query | Answer & Citations | pgvector | Read-Only | No | ✅ Implemented |
| **Database** | Semantic Text-to-SQL querying | Text question | Tabular records & summary| SQL Guard, Engine | Read-Only | No | ✅ Implemented |
| **Vision** | Image inspection & OCR | JPEG, PNG, WEBP | Findings, OCR text, bboxes| Tesseract, YOLO | No | No | ✅ Implemented |
| **Reasoning** | Cross-modal conflict resolution | Multi-agent outputs | Factual reconciliation | None (Internal) | No | No | ✅ Implemented |
| **Action** | Enterprise system actuation | Normalized payload | Execution result & verify | SMTP, Jira, ERP | Read/Write | Yes (>= MEDIUM)| ✅ Implemented |

---

# 74. API Authorization Matrix

Complete mapping of all 49 FastAPI endpoints to HTTP method, authentication requirement, required role, and tenant isolation:

| Endpoint Path | Method | Auth Required | Required Role / Permission | Tenant Scoped | Status |
| :--- | :---: | :---: | :--- | :---: | :---: |
| `/api/v1/auth/login` | POST | None | Public | N/A | ✅ Implemented |
| `/api/v1/users/me` | GET | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/chat` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/chat/` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/chat/conversations/{id}/messages` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/documents` | GET | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/documents/upload` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/documents/{id}` | GET | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/documents/{id}/index` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/agents/vision/upload` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/agents/vision/images` | GET | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/agents/vision/images/{id}` | GET | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/agents/vision/analyze` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/agents/supervisor/analyze` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/agents/document/analyze` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/agents/rag/query` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/agents/database/query` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/agents/reasoning/analyze` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/agents/run` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/agents/action/execute` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/agents/action/approvals` | GET | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/agents/action/approvals/{id}/approve` | POST | Bearer JWT | `Admin`, `Supervisor` | Yes | ✅ Implemented |
| `/api/v1/agents/action/approvals/{id}/reject` | POST | Bearer JWT | `Admin`, `Supervisor` | Yes | ✅ Implemented |
| `/api/v1/agents/action/history` | GET | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/approvals/{id}/decide` | POST | Bearer JWT | `Admin`, `Supervisor` | Yes | ✅ Implemented |
| `/api/v1/orchestration/run` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/orchestration/{id}/status` | GET | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/orchestration/{id}/events` | GET | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/orchestration/{id}/resume` | POST | Bearer JWT | `Admin`, `Supervisor` | Yes | ✅ Implemented |
| `/api/v1/orchestration/{id}/cancel` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/workflows` | POST | Bearer JWT | `Admin`, `Supervisor` | Yes | ✅ Implemented |
| `/api/v1/workflows` | GET | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/workflows/{id}` | GET | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/workflows/{id}` | PUT | Bearer JWT | `Admin`, `Supervisor` | Yes | ✅ Implemented |
| `/api/v1/workflows/{id}` | DELETE | Bearer JWT | `Admin` | Yes | ✅ Implemented |
| `/api/v1/workflows/{id}/run` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/workflows/{id}/runs` | GET | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/workflow-runs/{id}` | GET | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/workflow-runs/{id}/resume` | POST | Bearer JWT | `Admin`, `Supervisor` | Yes | ✅ Implemented |
| `/api/v1/workflow-runs/{id}/cancel` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/integrations` | GET | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/multimodal/analyze` | POST | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/notifications` | GET | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/analytics/overview` | GET | Bearer JWT | Any authenticated role | Yes | ✅ Implemented |
| `/api/v1/health` | GET | None | Public | No | ✅ Implemented |
| `/api/v1/openapi.json` | GET | None | Public | No | ✅ Implemented |
| `/api/v1/docs` | GET | None | Public | No | ✅ Implemented |
| `/api/v1/redoc` | GET | None | Public | No | ✅ Implemented |
| `/docs/oauth2-redirect` | GET | None | Public | No | ✅ Implemented |

---

# 75. Database Model Inventory

Complete inventory of all 27 SQLAlchemy ORM models from `Base.metadata`:

| # | Model Class | Table Name | Purpose | Primary Key | Tenant Scoped? | Key Relationships |
| :-: | :--- | :--- | :--- | :--- | :---: | :--- |
| 1 | `Organization` | `organizations` | Tenant organization boundary | UUID | N/A (Root) | Departments, Users, Documents |
| 2 | `Department` | `departments` | Organizational division | UUID | Yes (`organization_id`) | Users, Machines |
| 3 | `User` | `users` | Authenticated user account | UUID | Yes (`organization_id`) | Role, Department, Documents |
| 4 | `Role` | `roles` | RBAC role definition | UUID | Optional (NULL=System) | RolePermissions, Users |
| 5 | `Permission` | `permissions` | Granular capability | UUID | No (System-wide) | RolePermissions |
| 6 | `role_permissions` | `role_permissions`| Role-Permission junction table | Composite UUID | No | Role, Permission |
| 7 | `Document` | `documents` | Ingested file artifact | UUID | Yes (`organization_id`) | DocumentChunks, User |
| 8 | `DocumentChunk` | `document_chunks` | 1536-dim text vector chunk | UUID | Yes (`organization_id`) | Document |
| 9 | `Conversation` | `conversations` | Multi-turn chat thread | UUID | Yes (`organization_id`) | Messages, AgentRuns, User |
| 10 | `Message` | `messages` | Chat message & citations | UUID | Implicit (via Conv) | Conversation |
| 11 | `AgentRun` | `agent_runs` | Specialist execution trace | UUID | Yes (`organization_id`) | ToolCalls, Approvals, Conv |
| 12 | `ToolCall` | `tool_calls` | Tool invocation log | UUID | Implicit (via AgentRun)| AgentRun |
| 13 | `Approval` | `approvals` | Orchestrator approval record | UUID | Yes (`organization_id`) | AgentRun, WorkflowRun, Users |
| 14 | `AuditLog` | `audit_logs` | SHA-256 chained audit record | UUID | Yes (`organization_id`) | User |
| 15 | `Workflow` | `workflows` | Automation workflow template | UUID | Yes (`organization_id`) | WorkflowRuns, User |
| 16 | `WorkflowRun` | `workflow_runs` | Workflow execution instance | UUID | Yes (`organization_id`) | Workflow, Approvals |
| 17 | `ActionRecord` | `actions` | Action execution record | UUID | Yes (`organization_id`) | ActionApprovals, User |
| 18 | `ActionApproval`| `action_approvals`| Action Agent specific approval| UUID | Yes (`organization_id`) | Action, Users |
| 19 | `ActionAuditLog`| `action_audit_logs`| Action-specific audit record | UUID | Yes (`organization_id`) | User |
| 20 | `Machine` | `machines` | Manufacturing equipment | UUID | Yes (`organization_id`) | ProductionRecords, Maintenance|
| 21 | `ProductionRecord`| `production_records`| Manufacturing batch record | UUID | Yes (`organization_id`) | Machine |
| 22 | `Order` | `orders` | Sales/procurement order | UUID | Yes (`organization_id`) | Organization |
| 23 | `Product` | `products` | Product catalog item & SKU | UUID | Yes (`organization_id`) | Organization |
| 24 | `Vendor` | `vendors` | Supplier directory & ratings | UUID | Yes (`organization_id`) | Organization |
| 25 | `MaintenanceRequest`| `maintenance_requests`| Machine repair ticket | UUID | Yes (`organization_id`) | Machine |
| 26 | `Notification` | `notifications` | In-app user alert | UUID | Yes (`organization_id`) | User |
| 27 | `Integration` | `integrations` | Encrypted third-party config | UUID | Yes (`organization_id`) | Organization |

---

# 76. File and Folder Reference

| Path | Primary Responsibility |
| :--- | :--- |
| `backend/app/main.py` | FastAPI application factory, middleware registration, global exception handler |
| `backend/app/core/config.py` | Type-safe settings parsed from environment variables via Pydantic Settings |
| `backend/app/core/security.py` | Cryptographic utilities: bcrypt hashing, JWT issuance and decoding |
| `backend/app/core/middleware.py` | Request trace ID injection (`X-Request-ID`) and latency duration tracking |
| `backend/app/orchestration/graph.py` | LangGraph workflow compiler, state graph transitions, execution orchestrator |
| `backend/app/orchestration/nodes.py` | 12 discrete execution nodes for the cognitive orchestration lifecycle |
| `backend/app/orchestration/router.py` | Conditional edge routing logic for LangGraph state machine |
| `backend/app/services/chat_service.py` | Coordinates multi-agent chat sessions, message persistence, and approvals |
| `backend/app/services/document_service.py`| Handles file validation, storage persistence, and document intelligence |
| `backend/app/services/action_service.py` | Action Agent execution coordinator, approval transitions, and audit records |
| `agents/supervisor/agent.py` | Supervisor Agent intent classification, priority assignment, and DAG planning |
| `agents/database/security.py` | Zero-trust SQL security validator (read-only enforcement, catalog blocking) |
| `agents/vision/security.py` | Vision security validator (path traversal defense, prompt injection detection) |
| `agents/action/approval.py` | HMAC-SHA256 signature generator, payload hasher, and expiration verifier |
| `automation/engine/engine.py` | Workflow execution runtime managing sequential step loops and approval pauses |
| `frontend/src/App.tsx` | Main frontend React application shell, layout, and route definitions |
| `frontend/src/services/api/client.ts` | Axios HTTP client configured with JWT authorization interceptors |
| `docker-compose.yml` | Multi-container Docker deployment specification (6 services) |

---

# 77. Request Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User as Enterprise User
    participant Browser as React Frontend
    participant Nginx as Nginx Gateway
    participant FastAPI as FastAPI Backend
    participant Auth as Auth & RBAC
    participant Orch as LangGraph Orchestrator
    participant Agent as Specialist Agent
    participant DB as PostgreSQL / pgvector

    User->>Browser: Submit Instruction / Prompt
    Browser->>Nginx: POST /api/v1/chat (Bearer JWT)
    Nginx->>FastAPI: Proxy pass request
    FastAPI->>Auth: Validate JWT & User Status
    Auth-->>FastAPI: UserContext (id, org_id, role)
    FastAPI->>Orch: orchestrator.execute(state)
    Orch->>Orch: Supervisor Intent Classification
    Orch->>Agent: Dispatch to Specialist (RAG/DB/Vision)
    Agent->>DB: Execute Query / Vector Search (WHERE org_id)
    DB-->>Agent: Raw Records / Document Chunks
    Agent-->>Orch: Factual Findings & Citations
    Orch->>Orch: Evaluate Result & Format Grounded Answer
    Orch-->>FastAPI: Return UnifiedChatResponse
    FastAPI-->>Nginx: Return HTTP 200 JSON Envelope
    Nginx-->>Browser: Deliver JSON Response
    Browser-->>User: Render Grounded Answer & Citations
```

---

# 78. Chat Lifecycle

1. User sends message in `frontend/src/pages/Chat/`.
2. Client appends temporary message to UI and dispatches `POST /api/v1/chat`.
3. Server records user message in `messages` table associated with `conversation_id`.
4. Orchestrator initializes state, processes user attachments (PDF, images), and passes query through Supervisor Agent.
5. If specialist agents collect facts, citations are formatted and stored with the message.
6. The assistant's verified response is committed to the database and returned to the client.

---

# 79. Document Lifecycle

1. User selects document in `frontend/src/pages/Documents/`.
2. Client issues `POST /api/v1/documents/upload` as multipart form-data.
3. Server validates size (`<= 25MB`) and extension (`.pdf`, `.docx`, `.txt`).
4. File is saved to storage, SHA-256 checksum is computed, and `documents` record is created with status `UPLOADED`.
5. Background worker or `POST /api/v1/documents/{id}/index` chunks document into 500-token blocks.
6. Vector embeddings (1536-dim) are computed and inserted into `document_chunks`.
7. Document status transitions to `INDEXED`.

---

# 80. RAG Lifecycle

1. Query arrives at RAG Agent.
2. Embedding vector is generated via `text-embedding-3-large`.
3. Vector search executes against `document_chunks` using cosine distance with mandatory `organization_id` filter.
4. Top 5 chunks exceeding `0.05` similarity threshold are assembled into context.
5. Grounded prompt instructs LLM to answer strictly from context.
6. Factual assertions are cross-referenced to chunk metadata, and exact citations are generated.

---

# 81. Database Query Lifecycle

1. Natural language query arrives at Database Agent.
2. Agent consults `ApprovedTableSchema` for table structures and foreign keys.
3. Agent writes a `SELECT` query incorporating parameterized tenant filters (`:organization_id`).
4. `SecurityValidator` verifies read-only rules and system catalog prohibitions.
5. Query executes against PostgreSQL with a 10-second timeout and 100-row limit.
6. Tabular results are converted to markdown tables and summarized.

---

# 82. Vision Lifecycle

1. Image is uploaded via `POST /api/v1/agents/vision/upload`.
2. Dimensions verified (`<= 4096 x 4096`), format verified (JPEG/PNG/WEBP).
3. Image normalized to RGB, EXIF stripped.
4. OCR engine extracts text blocks and coordinates.
5. Object detector identifies operational equipment and defects.
6. Extracted text scanned for prompt injection attempts.
7. Findings encapsulated inside untrusted delimiters and returned as structured JSON.

---

# 83. Reasoning Lifecycle

1. Multi-modal query decomposed into discrete specialist tasks.
2. Concurrently invokes downstream specialist agents.
3. Collects and normalizes evidence into standardized `Evidence` structures.
4. Executes conflict detection algorithm to identify contradictions between modalities.
5. Synthesizes a unified, grounded conclusion without exposing internal chain-of-thought tokens.

---

# 84. Action Lifecycle

1. Action proposal received by Action Agent.
2. Idempotency key verified against `actions` table.
3. Role authorization validated via `ToolPermissionGuard`.
4. Risk evaluated: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
5. If `LOW`, dispatched immediately to tool connector.
6. If `>= MEDIUM`, approval record generated and execution suspended.
7. Following approval, tool executed, side effect verified, and SHA-256 audit entry logged.

---

# 85. Approval Lifecycle

```mermaid
flowchart TD
    ActionProposal["Action Proposed by Agent"] --> RiskGate{"Risk >= MEDIUM?"}
    
    RiskGate -->|No| AutonomousDispatch["Execute Tool Immediately"]
    RiskGate -->|Yes| ComputeHash["Compute SHA-256 Payload Hash<br/>(org_id + user_id + payload)"]
    
    ComputeHash --> InsertApproval["Insert ActionApproval Record<br/>Status: PENDING<br/>Set 30-min Expiration"]
    InsertApproval --> SuspendRun["Pause Orchestrator Workflow<br/>Status: WAITING_FOR_APPROVAL"]
    
    SuspendRun --> NotifyManager["Notify Organization Supervisor / Admin"]
    NotifyManager --> ManagerDecision{"Manager Decision<br/>in Approvals UI"}
    
    ManagerDecision -->|Reject| RecordReject["Update Status: REJECTED<br/>Log Rejection Reason<br/>Abort Execution"]
    ManagerDecision -->|Approve| CheckExpiry{"Approval Expired?<br/>(> 30 minutes)"}
    
    CheckExpiry -->|Yes| ExpireApproval["Mark Status: EXPIRED<br/>Reject Execution"]
    CheckExpiry -->|No| SignHMAC["Generate HMAC-SHA256 Signature<br/>Verify Payload Hash Integrity"]
    
    SignHMAC --> ResumeExecution["Resume Orchestrator Workflow<br/>Dispatch Authorized Action"]
    ResumeExecution --> PostVerify["Verify External System Result"]
    PostVerify --> LogAudit["Write SHA-256 Chained Audit Record"]
```

---

# 86. Workflow Lifecycle

1. Workflow triggered via API, schedule, or database event.
2. `WorkflowEngine` initializes `WorkflowRunState` with `PENDING` status.
3. Iterates through workflow DAG steps using `StepExecutor`.
4. If a step involves a medium/high risk action, run transitions to `WAITING_FOR_APPROVAL` and pauses.
5. Upon approval via `POST /api/v1/workflow-runs/{id}/resume`, execution resumes from the paused step.
6. Step outputs appended to context; status transitions to `COMPLETED`.

---

# 87. End-to-End Data Flow

Data flows through OmniAgent AI with clear boundaries between untrusted inputs and secure storage:
1. **Client Tier**: User input (prompts, uploaded documents, images) enters via HTTPS.
2. **Gateway Tier**: Nginx terminates TLS and proxies requests.
3. **Application Tier**: FastAPI validates data structures using Pydantic. Passwords hashed with bcrypt; access tokens verified with HS256.
4. **Cognitive Tier**: Prompts and context processed by LLMs. Extracted text wrapped in non-executable delimiters.
5. **Data Persistence Tier**: Relational data written to PostgreSQL; vectors to pgvector; files to MinIO. All stores partitioned by `organization_id`.
6. **Audit Tier**: State mutations written to immutable audit logs with SHA-256 hash verification.

---

# 88. End-to-End Security Flow

Security is enforced sequentially at every step of processing:
1. Network boundary: TLS encryption + Nginx reverse proxy.
2. Authentication boundary: OAuth2 Bearer JWT token verification.
3. Authorization boundary: 6-tier RBAC role check (`require_role`).
4. Tenant boundary: Mandatory `organization_id` foreign key validation.
5. Input boundary: Pydantic schema validation, file size/extension enforcement.
6. AI safety boundary: Adversarial prompt injection regex scanning, untrusted data delimiters.
7. Database boundary: Read-only SELECT enforcement, catalog blocking, parameterized queries.
8. Actuation boundary: Deterministic approval gating, HMAC-SHA256 signatures, 30-min expiration.
9. Audit boundary: Cryptographic SHA-256 hash chaining of audit ledger entries.

---

# 89. End-to-End Deployment Flow

1. Developer pushes code to `main` branch on GitHub.
2. GitHub Actions CI pipeline (`ci.yml`, `backend-tests.yml`) triggers.
3. Unit and integration test suites execute against ephemeral PostgreSQL 16 + pgvector containers.
4. Frontend build and TypeScript type-checking run via `npm run build`.
5. Upon successful build, Vercel pulls frontend changes and deploys SPA to global CDN.
6. Render builds backend Docker image (`infrastructure/docker/Dockerfile.backend`) and restarts API containers.
7. Backend executes `alembic upgrade head` against Supabase PostgreSQL database.
8. Render and AWS ECS verify container health via `GET /api/v1/health`.

---

# 90. Known Limitations

In the interest of full technical transparency, the following architectural limitations exist in the current codebase:

1. **Multimodal Audio & Video Scaffolding**: Audio transcription (`multimodal/audio/transcriber.py`) and video analysis (`multimodal/video/analyzer.py`) currently utilize mock/scaffolding providers. Integration with live Whisper and OpenCV video pipelines is planned.
2. **Vector Reranking Pass-Through**: The reranking module (`backend/app/services/rag/retrieval/reranking.py`) currently truncates results to `top_k` without cross-encoder or reciprocal rank fusion scoring.
3. **Local Storage Default**: The default object storage provider is configured to `local` filesystem storage. MinIO or AWS S3 must be explicitly configured via `STORAGE_PROVIDER=minio` for distributed environments.
4. **Synchronous Tool Adapters**: Certain third-party tool adapters (ERP, Slack) execute synchronously inside Celery tasks rather than utilizing fully asynchronous event buses.

---

# 91. Future Improvements

The following architectural enhancements are planned for future platform releases:

1. **Production Speech & Video Pipelines**: Integration of OpenAI Whisper ASR for real-time voice dictation and native OpenCV keyframe extraction for live video inspection.
2. **Advanced Cross-Encoder Reranking**: Implementation of Cohere / BGE cross-encoder rerankers to improve RAG precision.
3. **Server-Sent Events (SSE) Streaming**: Full token-by-token streaming for the unified chat endpoint (`/api/v1/chat`).
4. **Distributed Redis Event Bus**: Event-driven inter-agent communication using Redis Streams or Apache Kafka.
5. **Multi-Region Active-Active Database**: Distributed PostgreSQL clustering with read replicas across cloud regions.

---

# 92. Resume/Portfolio Project Summary

### Professional Resume Description

**OmniAgent AI — Enterprise Multimodal AI Employee & Automation Platform**
*Lead Architect & Full-Stack AI Engineer | React 18, TypeScript, FastAPI, PostgreSQL 16, pgvector, LangGraph, Docker*

- Engineered an enterprise-grade multimodal autonomous AI employee platform coordinating specialized agents (Vision, Document, RAG, Database, Reasoning, Action) via LangGraph state machines.
- Architected a zero-trust Text-to-SQL engine with automated read-only validation, system catalog blocking, and mandatory tenant filtering across PostgreSQL business tables.
- Built a high-performance RAG pipeline leveraging PostgreSQL 16 `pgvector` with 1536-dimensional embeddings, cosine similarity search, and exact document citation generation.
- Implemented a Human-in-the-Loop governance engine featuring 4-tier risk classification, SHA-256 payload hashing, HMAC-SHA256 signature verification, and 30-minute automated approval expiration.
- Designed complete logical multi-tenancy across 27 database models, reinforced by a 6-tier Role-Based Access Control (RBAC) hierarchy and SHA-256 hash-chained immutable audit ledgers.
- Deployed a production cloud architecture utilizing Vercel (React 18 SPA), Render/AWS ECS (FastAPI Backend), Supabase (Managed PostgreSQL + pgvector), and Redis 7 with comprehensive CI/CD test automation.

---

# 93. Interview Preparation

### Technical Q&A Based on Actual Implementation

#### Q1: Why did you choose FastAPI over Flask or Django?
**Answer**: FastAPI natively supports asynchronous Python (`async`/`await`), which is crucial when orchestrating concurrent agent operations, embedding generation, vector searches, and LLM API calls. Additionally, FastAPI provides automated Pydantic v2 data validation and built-in OpenAPI 3.0 documentation generation.

#### Q2: Why use LangGraph instead of standard LangChain chains or AutoGen?
**Answer**: Enterprise workflows are cyclical and stateful, requiring loops, conditional routing, and explicit human intervention points. LangGraph models workflows as stateful directed graphs (`StateGraph(OrchestrationState)`), allowing us to pause graph execution when human approval is required (`WAITING_FOR_APPROVAL`) and resume seamlessly once signed off.

#### Q3: How do you prevent SQL injection and unauthorized data modification in the Database Agent?
**Answer**: We implement a multi-layered zero-trust validator (`SecurityValidator`). First, queries must begin with `SELECT` or `WITH`. Second, we use regex token matching to block all DDL and DML statements (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`). Third, we block access to PostgreSQL system catalogs (`pg_catalog`, `information_schema`). Finally, we mandate that every query must explicitly reference `organization_id` in its `WHERE` clause and bind the authenticated user's organization ID.

#### Q4: How is tenant isolation enforced in vector search?
**Answer**: Our `document_chunks` table includes an `organization_id` foreign key. The `VectorSearch.search()` method explicitly requires `org_id` and adds `.where(DocumentChunk.organization_id == org_id)` directly to the SQL query. PostgreSQL evaluates this condition before or alongside vector cosine distance ranking, mathematically guaranteeing that candidate chunks from other tenants are never examined.

#### Q5: How does the Human-in-the-Loop approval mechanism prevent parameter tampering?
**Answer**: When an action is proposed, we compute a SHA-256 hash of the normalized payload combined with `organization_id` and `user_id`. When a manager approves the request, we record the decision with an HMAC-SHA256 signature generated using `SECRET_KEY`. Before executing the action, the backend re-computes the payload hash and compares it against the stored approval record using `hmac.compare_digest()`, ensuring that modified payloads are immediately rejected.

#### Q6: How are LLM hallucinations mitigated in the RAG pipeline?
**Answer**: We enforce strict context grounding. Chunks must exceed a minimum cosine similarity threshold (`0.05`). The system prompt instructs the model to answer exclusively using provided context. If insufficient context is retrieved, the agent returns an explicit fallback message. Every factual claim is tagged with verified citations linking to document UUID, page number, and section.

#### Q7: Why did you choose PostgreSQL with pgvector instead of a standalone vector database like Pinecone or Milvus?
**Answer**: Standalone vector databases introduce operational complexity, dual-write consistency issues, and cross-system latency. With `pgvector`, our relational business data and vector embeddings live inside the same ACID-compliant PostgreSQL 16 database. This enables unified transactions, simplified backups via `pg_dump`, and native relational joins between vector chunks and tenant organization records.

#### Q8: How does the frontend handle token authentication and expired sessions?
**Answer**: The frontend uses Axios interceptors (`frontend/src/services/api/client.ts`). Every outgoing request attaches the JWT Bearer token from Zustand persistent storage. If the backend returns a 401 Unauthorized status, the response interceptor catches the error, purges expired tokens from local storage, and redirects the user to the `/login` portal.

---

# 94. Developer Guide

### Adding a New Specialist Agent
1. Create agent directory: `agents/my_agent/`.
2. Define Pydantic schemas in `agents/my_agent/schemas.py`.
3. Implement core logic in `agents/my_agent/agent.py`.
4. Register the new agent in `backend/app/orchestration/nodes.py`.
5. Update `SupervisorAgent` prompts in `agents/prompts/supervisor/orchestration.py` to recognize the new agent's capabilities.
6. Mount a direct test endpoint in `backend/app/api/v1/agents.py`.

### Adding a New Enterprise Tool
1. Create tool implementation in `tools/<category>/my_tool.py`.
2. Register the tool function in `ToolRegistry` (`tools/common/registry.py`).
3. Add role permissions for the tool in `ToolPermissionGuard.TOOL_PERMISSIONS` (`tools/common/permissions.py`).
4. Update the Action Agent registry in `agents/action/registry.py`.

### Adding a New Database Model
1. Define model class in `backend/app/models/my_model.py` inheriting from `Base`.
2. Ensure model includes `organization_id = Column(UUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)`.
3. Import the model in `backend/app/models/__init__.py`.
4. Generate Alembic migration:
   ```bash
   cd backend
   alembic revision --autogenerate -m "add_my_model_table"
   alembic upgrade head
   ```

---

# 95. Final Production Checklist

Prior to production deployment, verify all checklist items:

- [ ] Master `SECRET_KEY` rotated to a secure 64-character secret.
- [ ] `DEBUG` set to `false` in production environment.
- [ ] `DATABASE_URL` configured with valid SSL mode (`?ssl=require`).
- [ ] PostgreSQL `pgvector` extension enabled (`CREATE EXTENSION IF NOT EXISTS vector;`).
- [ ] All Alembic migrations applied (`alembic upgrade head`).
- [ ] `ALLOWED_ORIGINS` restricted strictly to production client domains.
- [ ] Production LLM API keys configured (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).
- [ ] SMTP server configured with valid credentials for email actuation.
- [ ] MinIO or AWS S3 credentials configured for distributed document storage.
- [ ] Background Celery workers active and connected to Redis broker.
- [ ] Automated database backup cron active (`infrastructure/scripts/backup.sh`).
- [ ] System health check returns HTTP 200 (`GET /api/v1/health`).
- [ ] Automated security test suite passes (`pytest tests/security/ -v`).
- [ ] Frontend production build generated without errors (`npm run build`).

---
'''
