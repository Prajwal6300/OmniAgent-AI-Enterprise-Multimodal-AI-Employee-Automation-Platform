# OmniAgent AI — System Architecture Specification

## 1. High-Level Architecture Overview

OmniAgent AI is an enterprise-grade autonomous AI employee and orchestration platform designed to securely coordinate multi-agent cognitive tasks, document intelligence, transactional approvals, and resilient workflows within strict tenant boundaries.

```
                              ┌────────────────────────────────────────┐
                              │            Vercel Frontend             │
                              │   React 18 / Vite / Zustand / Tailwind  │
                              └───────────────────┬────────────────────┘
                                                  │ HTTPS / SSE
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                Render Backend (Docker Web Service)                           │
│                                                                                              │
│   ┌──────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        FastAPI REST API & SSE Gateway (/api/v1)                      │   │
│   │  • Multi-tenant middleware (organization_id scoping)   • Rate limiting & CORS        │   │
│   │  • Cryptographic JWT & refresh token interceptors      • Request trace recording     │   │
│   └──────────────────────────────────────────┬───────────────────────────────────────────┘   │
│                                              │                                               │
│   ┌──────────────────────────────────────────▼───────────────────────────────────────────┐   │
│   │                         LangGraph Cognitive Orchestrator                             │   │
│   │  • Intent analysis & capability routing      • Human-in-the-loop pause & resume     │   │
│   │  • Multi-agent consensus & conflict solver   • Cryptographic state transitions       │   │
│   └──────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬────┘   │
│          │              │              │              │              │              │        │
│   ┌──────▼──────┐┌──────▼──────┐┌──────▼──────┐┌──────▼──────┐┌──────▼──────┐┌──────▼──────┐ │
│   │ Supervisor  ││  Document   ││     RAG     ││   Database  ││    Vision   ││   Action   │ │
│   │   Agent     ││    Agent    ││    Agent    ││    Agent    ││    Agent    ││   Agent    │ │
│   └─────────────┘└─────────────┘└─────────────┘└─────────────┘└─────────────┘└─────────────┘ │
└──────────────────────────────────────────────┬───────────────────────────────────────────────┘
                                               │
             ┌─────────────────────────────────┼─────────────────────────────────┐
             │                                 │                                 │
             ▼                                 ▼                                 ▼
┌──────────────────────────┐     ┌──────────────────────────┐     ┌──────────────────────────┐
│   Supabase PostgreSQL    │     │     Render Key Value     │     │     Supabase Storage     │
│   - pgvector 1536 cosine │     │     - Celery broker      │     │     - S3-compatible API  │
│   - tsvector full-text   │     │     - Distributed locks  │     │     - Encrypted chunks   │
│   - Cryptographic audit  │     │     - Rate limit counter │     │     - Tenant prefix keys │
│   - Multi-tenant cascade │     │     - Token revocation   │     │     - SHA-256 checksums  │
└──────────────────────────┘     └──────────────────────────┘     └──────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 Multi-Agent Cognitive Mesh (`backend/app/agents/`)
- **Supervisor Agent**: LangGraph router performing intent extraction, priority assignment, and DAG routing using OpenAI structured outputs.
- **Document Agent**: Extracts structured text and metadata from PDF, DOCX, and text assets using `pypdf` and `python-docx` with strict sequential page caps to eliminate OOM vulnerabilities.
- **RAG Agent**: Implements dense vector retrieval over `pgvector(1536)` and lexical retrieval over PostgreSQL `tsvector`, combined via Reciprocal Rank Fusion (RRF, k=60) with span-level citation binding.
- **Database Agent**: Translates natural language questions to read-only SQL, verified via `sqlglot` AST parsing enforcing table allow-lists, strict tenant filters, and blocking all DDL/DML.
- **Vision Agent**: Multimodal visual inspection powered by OpenAI GPT-4o vision with image magic-byte verification, pixel dimension clamps, and binary OCR detection.
- **Reasoning Agent**: Multi-source evidence reconciliation, cross-verifying outputs from distinct specialists to eliminate hallucinations.
- **Action Agent**: Executes authorized enterprise side-effects (tickets, emails, reports, notifications) guarded by dual-approver policies for `CRITICAL` risk and cryptographic payload bindings.

### 2.2 Automation & Workflow Engine (`backend/app/automation/`)
- **Engine**: Stateful DAG workflow runner persisting step transitions, execution retries, and checkpointed intermediate state to PostgreSQL.
- **Triggers**: Event-driven triggers including `ManualTrigger`, `ScheduleTrigger` (cron-based), and `WebhookTrigger`.
- **Conditions**: Deterministic expression evaluator without dynamic code execution (`eval`), evaluating operational rules against step payloads.

### 2.3 Object Storage Layer (`backend/app/tools/storage/` & `services/storage_service.py`)
- **Production Provider**: Supabase Object Storage using standard S3-compatible credentials (`SUPABASE_S3_*`), scoped to tenant directories with SHA-256 checksum verification.
- **Development Fallback**: `LocalStorageService` writing to isolated directory structures. The backend strictly refuses to boot in production if `STORAGE_PROVIDER=local`.

---

## 3. Technology Stack Specification

| Component | Standard Technology | Rationale |
|---|---|---|
| **Language & Runtime** | Python 3.11 / 3.13 | High performance async runtime with strict typing |
| **API Framework** | FastAPI 0.115+ | High throughput async ASGI framework with OpenAPI generation |
| **Agentic Framework** | LangGraph & LangChain Core | Deterministic cyclical graph orchestration and state management |
| **Primary Database** | PostgreSQL 16 + `pgvector` | Unified relational schema and cosine vector embeddings |
| **Cache & Task Broker** | Redis 7 | Distributed locking, rate limiting, and task queues |
| **Object Storage** | Supabase Storage (S3 API) | Managed S3-compatible cloud storage with tenant isolation |
| **Frontend Framework** | React 18 + Vite + TailwindCSS | Fast reactive SPA with TanStack Query and Zustand stores |
| **Hosting & Deployments** | Render (Backend) + Vercel (Frontend) | Zero-maintenance cloud deployment with TLS termination |
