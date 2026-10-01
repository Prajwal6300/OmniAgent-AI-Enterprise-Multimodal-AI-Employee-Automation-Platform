# OmniAgent AI — Production Cleanup & Restructure Report (Step 1 & Step 2 Plan)

**Date**: 2026-10-01  
**Author**: Senior Staff Engineer  
**Branch**: `chore/production-ready`  
**Baseline Git Tag**: `pre-cleanup`  
**Status**: Step 1 Complete & Verified — Executing Step 2  

---

## 1. Executive Summary & Stack Enforcement

The target production stack for OmniAgent AI is strictly fixed:
- **LLM + Embeddings + Vision + Audio**: OpenAI API only (`OPENAI_API_KEY`)
  - Chat/Reasoning/Supervisor: `gpt-4o` (or configured OpenAI model)
  - Embeddings: `text-embedding-3-large` (`dimensions=1536`)
  - Vision: OpenAI GPT-4o multimodal vision
  - Audio: OpenAI Whisper (`whisper-1`) + `ffmpeg` normalization
- **Frontend Hosting**: Vercel (Single-Page App, Vite, React 18, TanStack Query, TailwindCSS)
- **Backend Hosting**: Render (Docker web service + background Celery worker + Celery beat)
- **Database**: Supabase PostgreSQL with `pgvector` (`vector_cosine_ops`, HNSW indexing, tsvector full-text search)
- **Redis**: Render Key Value (or Upstash) for Celery broker, Celery results, distributed locks, rate limits, token revocations
- **Object Storage**: Supabase Storage (S3-compatible API with `SUPABASE_S3_*` credentials) + fallback `local` provider for offline development only (app refuses to boot with `local` when `ENVIRONMENT=production`)

Every component outside this stack (MinIO, AWS ECS/CloudFormation, Cohere rerankers, Anthropic SDK paths, Prometheus/Grafana, SAP/Oracle mock stubs, and frontend placeholder pages) will be removed or consolidated.

---

## 2. Architectural Decisions

### 2.1 Audio Decision
- **Choice**: Option (b) — Remove audio entirely, including `multimodal/audio/`, worker task stubs, and documentation mentions.
- **Rationale**: The previous audio transcriber was an unbacked dummy stub returning static strings. In accordance with strict zero-stub and zero-mock production requirements, audio has been completely removed from the backend and frontend. Voice page and audio routes have been removed.

### 2.2 ERP & Action Types Removal
- Remove `tools/erp/` (`sap.py`, `oracle.py`, `client.py`).
- Remove `ERP_WRITE` from `ActionType` enum, risk policies, schemas, UI, docs, and tests.
- Retain `HIGH` and `CRITICAL` risk gates for remaining real actions (database writes, storage delete, external ticket creation, email dispatch).

### 2.3 Test Double & Mock Provider Extraction
- All deterministic test doubles (e.g. deterministic embedding provider) extracted to `backend/tests/fixtures/embeddings.py`.
- Production code must never import from `tests/` or contain "mock" implementations.
- Enforce via an automated import-linter test.

### 2.4 Container & Compose Strategy
- Create `backend/Dockerfile`: multi-stage, non-root user, pinned Debian/Python, includes ffmpeg, poppler, tesseract.
- Create `frontend/Dockerfile`: multi-stage Vite build + minimal Nginx for local `docker compose up`.
- Update `docker-compose.yml` to remove MinIO, remove deleted paths, and run postgres+pgvector, redis, backend, worker, frontend.

---

## 3. KEEP List (Categorized as [EXISTS] vs [TO BUILD])

### 3.1 Backend APIs & Endpoints (`backend/app/api/v1/`)
- `auth.py`:
  - `[EXISTS]` `/auth/login` (Standard username/password authentication)
  - `[TO BUILD]` `/auth/register` (Creates organization and Owner; subsequent registrations invite-only)
  - `[TO BUILD]` `/auth/refresh` (Refresh-token rotation with Redis revocation list)
  - `[TO BUILD]` `/auth/logout` (Revokes refresh token in Redis)
- `users.py`:
  - `[EXISTS]` `/users/me` (Profile retrieval)
  - `[TO BUILD]` `GET /users` (Tenant-scoped user listing)
  - `[TO BUILD]` `POST /users/invite` (Signed expiring token)
  - `[TO BUILD]` `POST /users/accept-invite`
  - `[TO BUILD]` `PUT /users/{id}/role` (Demotion protection for last Owner)
  - `[TO BUILD]` `DELETE /users/{id}` (Soft deactivate)
- `chat.py`:
  - `[EXISTS]` `POST /chat` (Basic conversation turn)
  - `[TO BUILD]` `GET/POST /chat/stream` (SSE event streaming with agent events, citations, inline approvals, disconnect handling)
- `documents.py`:
  - `[EXISTS]` Document upload, tenant storage, basic metadata
  - `[TO BUILD]` Strict magic-byte validation, sequential page limits to avoid OOM, pgvector chunk indexing
- `approvals.py`:
  - `[EXISTS]` `POST /approvals/{id}/decide`
  - `[TO BUILD]` Redis distributed locks (scoped to `approval_id`), dual-approver gating for CRITICAL actions, canonical JSON payload hashing
- `workflows.py`:
  - `[EXISTS]` `POST /workflows`, `POST /workflows/{id}/run`, `GET /workflows`
  - `[TO BUILD]` Step retries, timeouts, max-step enforcement, cancellation & resume
- `analytics.py`:
  - `[TO BUILD]` Replace stub returning 0s with real queries scoped by `organization_id` (tokens, cost, p50/p95/p99 latency, success rates, date ranges)
- `notifications.py`:
  - `[TO BUILD]` Replace stub returning `[]` with real tenant queries, filtering, mark read, mark all read, unread count
- `integrations.py`:
  - `[TO BUILD]` Replace stub returning `[]` with full CRUD, Fernet encryption at rest (`config_encrypted`), secret redaction, test-connection
- `health.py`:
  - `[EXISTS]` `/health` (Liveness)
  - `[TO BUILD]` `/ready` (Deep check: DB, Redis, pgvector extension, storage bucket, Alembic head)
- `orchestration.py`:
  - `[EXISTS]` Multi-agent orchestration API

### 3.2 Database Models & Storage
- `[EXISTS]` Models: `User`, `Role`, `Permission`, `Organization`, `Document`, `DocumentChunk`, `Approval`, `Workflow`, `WorkflowRun`, `AuditLog`, `ActionAuditLog`, `Integration`, `Notification`, `Conversation`, `Message`, `ToolCall`, `AgentRun`.
- `[TO BUILD]` Hash-chaining on audit logs (`prev_hash` column and `entry_hash = SHA256(prev_hash + canonical_payload)`).
- `[TO BUILD]` HNSW vector index (`vector_cosine_ops`) and GIN index for full-text search on `document_chunks`.
- `[TO BUILD]` Automated test introspecting `Base.metadata` verifying all tenant tables have `organization_id` FK with `ondelete="CASCADE"`.

### 3.3 Specialized AI Agents (`backend/app/agents/`)
- `supervisor`:
  - `[EXISTS]` LangGraph router
  - `[TO BUILD]` OpenAI structured outputs; remove mock fallbacks
- `document`:
  - `[EXISTS]` `agents/document/extractor.py` (pypdf + docx parsing)
  - `[TO BUILD]` Consolidate into `backend/app/processing/`, remove `MockDocumentLLMProvider`
- `rag`:
  - `[EXISTS]` Vector chunk schema and cosine search logic
  - `[TO BUILD]` Hybrid search (pgvector dense + tsvector full-text fused with RRF k=60), OpenAI structured reranker (top 20 -> top_k), span-level citation builder
- `database`:
  - `[EXISTS]` Basic SQL generation
  - `[TO BUILD]` Strict `sqlglot` AST validation (SELECT/WITH SELECT only, table allow-list, blocking system tables/DDL/DML, mandatory tenant predicate, LIMIT cap, read-only 10s timeout)
- `vision`:
  - `[EXISTS]` Image upload and analyzer outline
  - `[TO BUILD]` OpenAI GPT-4o vision integration; OCR and detector report `UNAVAILABLE` honestly if binaries are missing; remove `MockVisionProvider`
- `reasoning`:
  - `[EXISTS]` DAG orchestration structure
  - `[TO BUILD]` Grounded multi-source synthesis with OpenAI, zero chain-of-thought exposure to user, remove `MockReasoningLLMProvider`
- `action`:
  - `[EXISTS]` Risk classification, verifier
  - `[TO BUILD]` Redis distributed lock idempotency, dual distinct approvers for CRITICAL actions, remove fake test mock providers

### 3.4 Automation & Workflows (`backend/app/automation/`)
- `engine`:
  - `[EXISTS]` `WorkflowEngine` core loop
  - `[TO BUILD]` Durable state in Postgres surviving restarts, step retries, max steps
- `conditions`:
  - `[EXISTS]` Rule and operator evaluators
- `triggers`:
  - `[EXISTS]` `ManualTrigger`, `EventTrigger`, `ScheduleTrigger` in `base.py`
  - `[TO BUILD]` Webhook trigger with HMAC signature verification and replay protection

### 3.5 Processing Pipeline (`backend/app/processing/`)
- `[EXISTS]` PDF/DOCX extractors (from `agents/document/extractor.py`)
- `[TO BUILD]` Unified processing package:
  - `processing/pdf.py`: Safe sequential rasterization & extraction
  - `processing/docx.py`: python-docx extraction
  - `processing/image.py`: Magic bytes, dimension & pixel caps
  - `processing/ocr.py`: Pytesseract wrapper with binary detection

### 3.6 Production Tools (`backend/app/tools/`)
- `[EXISTS]` `ToolPermissionGuard`
- `[TO BUILD]` Unified tools package:
  - `tools/storage/`: Supabase S3-compatible client (production) + local disk client (development only)
  - `tools/email/`: Async SMTP with honest `NOT_CONFIGURED` status
  - `tools/tickets/`: Real HTTP-based webhook/API adapter with idempotency keys
  - `tools/reports/`: Real CSV / Excel generator

### 3.7 Workers & Celery (`backend/app/workers/`)
- `[TO BUILD]` `celery_app.py` instantiation with `task_acks_late=True`
- `[TO BUILD]` Real worker tasks: document indexing, workflow execution, email sending
- `[TO BUILD]` Beat schedule: workflow cron, 30-min approval SLA escalation, 15-min hung run watchdog

### 3.8 Frontend (15 Production Pages in `frontend/src/pages/`)
1. `Login`: `[EXISTS]` (Needs refresh-token handling)
2. `Register`: `[EXISTS]` (Needs backend `/auth/register` wiring)
3. `Dashboard`: `[EXISTS]`
4. `Chat`: `[EXISTS]` (Needs SSE streaming, citations, inline approvals, audio upload)
5. `Documents`: `[EXISTS]` (Needs audio/doc processing view)
6. `KnowledgeBase`: `[EXISTS]`
7. `ImageAnalysis`: `[EXISTS]`
8. `Approvals`: `[EXISTS]` (Needs dual-approver status display)
9. `Workflows`: `[EXISTS]`
10. `Analytics`: `[TO BUILD]` Recharts integration backed by real `/analytics/overview`
11. `Notifications`: `[TO BUILD]` Real listing, unread count badge, mark-read
12. `Integrations`: `[TO BUILD]` CRUD, test-connection modal, secret redaction
13. `Admin`: `[TO BUILD]` User management, role update, invite modal
14. `Settings`: `[EXISTS]`
15. `AgentRuns`: `[EXISTS]`

---

## 4. TO BUILD Master Checklist (For Part B Implementation)

- [ ] **Auth & User Management**:
  - [ ] `/auth/register` (new org + owner; invite-only afterwards)
  - [ ] `/auth/refresh` (rotation + Redis revocation)
  - [ ] `/auth/logout`
  - [ ] `/users` CRUD + `/users/invite` + `/users/accept-invite`
  - [ ] Protection: last Owner cannot be demoted/deleted
- [ ] **Security Hardening**:
  - [ ] `sqlglot` AST validation on SQL Agent (strict tenant predicate, SELECT only, block system schemas)
  - [ ] Redis distributed lock around approval decision and workflow resume
  - [ ] Dual approver requirement for CRITICAL actions
  - [ ] Hash-chained audit logs (`prev_hash` + SHA256 chain)
  - [ ] Fernet encryption for `integrations.config_encrypted`
  - [ ] Uniform prompt-injection defense across all input types
  - [ ] Upload validation: magic bytes, size cap, sequential PDF rasterization
  - [ ] Strict CORS, security headers, request body limits, rate limits
- [ ] **RAG & Agents**:
  - [ ] Hybrid search: pgvector dense + tsvector full-text + RRF (k=60)
  - [ ] OpenAI structured reranker (top 20 -> top_k)
  - [ ] Span-level claim-to-chunk citation alignment
  - [ ] SSE streaming `/chat/stream`
- [ ] **Workers & Orchestration**:
  - [ ] Celery app configuration & tasks
  - [ ] Celery Beat scheduler with DB-backed workflows
  - [ ] 30-min approval SLA escalation task
  - [ ] 15-min hung task watchdog
  - [ ] Webhook trigger with HMAC signature & replay protection
- [ ] **API & Frontend Completeness**:
  - [ ] `/analytics/overview` real queries
  - [ ] `/notifications` real queries and actions
  - [ ] `/integrations` full CRUD and connection test
  - [ ] `/ready` deep readiness probe
  - [ ] Complete frontend pages: Analytics, Notifications, Integrations, Admin
  - [ ] Zustand store consolidation with 401 refresh interceptor
- [ ] **Deployment & Testing**:
  - [ ] `deploy/render.yaml`
  - [ ] `deploy/supabase/` setup scripts
  - [ ] `scripts/preflight.py`
  - [ ] `scripts/backup.sh` & `restore.sh`
  - [ ] `backend/Dockerfile` & `frontend/Dockerfile`
  - [ ] Cross-tenant security test matrix & fuzz tests

---

## 5. REMOVE List (Proved Unused / Outside Fixed Stack)

| Target File / Directory | Category | Reason & Proof of Deletion |
|---|---|---|
| `docker-compose.yml` (MinIO service & volume) | Outside Stack | Stack uses Supabase Storage. MinIO service is obsolete. |
| `infrastructure/cloud/aws/` | Outside Stack | Stack is Render + Supabase + Vercel. AWS ECS task definition is unused. |
| `infrastructure/monitoring/grafana/` | Outside Stack | Stack uses structured JSON logging + Sentry. Grafana provisioning is dead. |
| `infrastructure/monitoring/prometheus/` | Outside Stack | Prometheus config is unused in Render container environment. |
| `infrastructure/nginx/nginx.conf` | Outside Stack | Render terminates TLS directly. Replaced by frontend local Dockerfile. |
| `infrastructure/docker/` | Outside Stack | Replaced by single multi-stage `backend/Dockerfile` and `frontend/Dockerfile`. |
| `agents/evaluation/` (`evaluators/`, `metrics/`, `datasets/`) | Scaffolding | Returns hardcoded `1.0` and `100.0` stubs. Not reachable from any user route. |
| `agents/memory/` (`long_term.py`, `short_term.py`, `working_memory.py`) | Scaffolding | Dummy in-memory list/dict and `pass` methods. Real memory is in Postgres. |
| `agents/graph/` (`graph.py`, `nodes.py`, `routing.py`, `state.py`) | Duplicate | Obsolete prototype duplicating `backend/app/orchestration/`. |
| `multimodal/video/` (`analyzer.py`, `frame_extractor.py`, `processor.py`) | Hollow Stub | Hardcoded stubs returning `["frame_001.jpg"]`. No real pipeline or backend route. |
| `multimodal/audio/` (`processor.py`, `transcriber.py`) | Hollow Stub | Hardcoded stubs returning dummy strings. Removed in accordance with Option (b). |
| `multimodal/documents/` (`docx.py`, `metadata.py`, `pptx.py`) | Duplicate | 5-line empty stubs. Consolidated into `agents/document/extractor.py`. |
| `multimodal/pdf/` (`extractor.py`, `parser.py`, `tables.py`) | Duplicate | Fake stubs returning dummy strings. Replaced by real `pypdf` extractor. |
| `multimodal/ocr/` (`engine.py`, `preprocessing.py`) | Duplicate | Fake stubs. Consolidated with `agents/vision/ocr.py`. |
| `multimodal/image/` (`classifier.py`, `processor.py`, `vision.py`) | Duplicate | Fake stubs. Consolidated with `agents/vision/`. |
| `multimodal/structured_data/` (`csv_processor.py`, `excel_processor.py`, `schema_inference.py`) | Duplicate | Consolidated into tools/processing. |
| `multimodal/text/` (`normalizer.py`, `processor.py`) | Scaffolding | Trivial regex helpers. Consolidated into `app/processing/text.py`. |
| `tools/erp/adapters/sap.py` | Fake Stub | Returns hardcoded ACME Corp PO. No real SAP connection exists. |
| `tools/erp/adapters/oracle.py` | Fake Stub | Returns hardcoded Global Tech PO. No real Oracle connection exists. |
| `tools/erp/client.py` | Fake Stub | Wrapper around the fake SAP/Oracle adapters. |
| `automation/actions/` (`api.py`, `database.py`, `email.py`, `notification.py`, `report.py`, `ticket.py`) | Fake Stubs | 2-line functions returning dummy `{"status": "SUCCESS"}` dicts. |
| `automation/triggers/database_event.py`, `email.py`, `file_upload.py`, `manual.py`, `schedule.py` | Redundant Stubs | Dummy classes with empty `trigger()` methods duplicating `base.py`. |
| `automation/workflows/` (`customer_support.py`, `hr.py`, `invoice.py`, `it_support.py`, `manufacturing.py`, `reporting.py`) | Fake Stubs | Classes containing only a static list of string names (`STEPS = [...]`). |
| `backend/app/services/rag/ingestion/loader.py` | Fake Stub | Hardcoded `return [{"text": "Extracted document content"}]`. |
| `backend/app/services/rag/ingestion/metadata.py` | Fake Stub | Trivial dummy enrichment. |
| `backend/debug_config.py` | Scratch Script | One-off debug script left in backend root. |
| `backend/debug_fk.py` | Scratch Script | One-off debug script left in backend root. |
| `backend/debug_tables.py` | Scratch Script | One-off debug script left in backend root. |
| `backend/gen_migration.py` | Scratch Script | One-off migration helper script left in backend root. |
| `backend/generate_migration.py` | Scratch Script | Duplicate migration generator script left in backend root. |
| `backend/inspect_metadata.py` | Scratch Script | One-off metadata inspection script left in backend root. |
| `backend/run_migration.py` | Scratch Script | One-off script left in backend root. |
| `backend/test_alembic.py` | Scratch Script | Loose test script causing pytest collection failures. |
| `backend/test_alembic_upgrade.py` | Scratch Script | Loose test script causing pytest collection failures. |
| `backend/test_vector.py` | Scratch Script | Loose test script causing pytest collection failures. |
| `frontend/src/pages/Video/` | Placeholder UI | Hollow card with no backend route. |
| `frontend/src/pages/Voice/` | Placeholder UI | Hollow card with no backend route; replaced by Chat/Documents audio upload. |
| `frontend/src/pages/Tasks/` | Placeholder UI | Hollow card duplicating Workflows/AgentRuns. |
| `frontend/src/pages/Agents/` | Placeholder UI | Hollow card duplicating Supervisor/Chat. |
| `md/` (root documentation folder) | Outdated Docs | 95+ speculative markdown files referencing AWS, MinIO, SAP, etc. Converted to clean `docs/`. |
| `test_output.txt` | Build Artifact | Root test log artifact. |
| Root `storage/` runtime directory | Local Runtime | Runtime uploaded files from previous dev runs. Added to `.gitignore`. |

---

## 6. REVIEW List (`_review_before_delete/` Candidates)

Moved via `git mv` into `_review_before_delete/`:
1. `agents/prompts/` (`action/execution.py`, `rag/qa.py`, `reasoning/reconciliation.py`, `supervisor/orchestration.py`, `system/base.py`, `system/safety.py`, `vision/inspection.py`)
2. `frontend/src/constants/routes.ts`
3. `frontend/src/services/analytics/analyticsService.ts`
4. `frontend/src/services/auth/authService.ts`
5. Deterministic embeddings fixture (extracted to `backend/tests/fixtures/embeddings.py` as a test fixture).
