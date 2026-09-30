"""
OmniAgent AI Documentation - Part 1 (Sections 1 to 16)
"""

def get_part1() -> str:
    return '''# 1. Project Overview

**OmniAgent AI** is a production-grade, enterprise-scale Multimodal Autonomous AI Employee and Workflow Automation Platform. Designed for modern digital operations, OmniAgent AI ingests and contextualizes cross-modal enterprise artifacts—ranging from scanned invoices, machine schematics, and audio dispatches to spreadsheets, relational database records, and live API feeds—and autonomously routes, reasons, executes, and audits complex enterprise workflows.

Unlike conventional conversational chatbots that produce passive, non-deterministic text responses, OmniAgent AI acts as an autonomous digital coworker. It coordinates specialized AI agents, interfaces directly with enterprise systems through deterministic, sandboxed tools, enforces strict Human-in-the-Loop (HITL) approval gates for elevated-risk operations, and maintains an immutable, cryptographically verifiable audit trail for regulatory compliance.

### The Problem Being Solved

Modern enterprise operations suffer from four foundational productivity and architecture bottlenecks:
1. **Modal Silos**: Enterprise knowledge is fractured across unstructured documents (PDFs, contracts, scanned receipts), visual feeds (schematics, equipment inspection photos), operational audio, spreadsheets, and SQL databases. Point solutions cannot synthesize answers across these disparate formats simultaneously.
2. **Fragile and Dangerous AI Actuation**: Naive LLM agent implementations (e.g. unconstrained ReAct loops) possess unrestricted access to database drivers or external APIs. This exposes the enterprise to SQL injection, prompt injection, catastrophic data corruption, unauthorized data exfiltration, and non-deterministic side effects.
3. **Lack of Human Governance**: Enterprise compliance frameworks (SOC 2 Type II, ISO 27001, HIPAA, GDPR) forbid autonomous software from modifying financial records, dispatching external communications, or modifying production states without explicit, attributable human authorization.
4. **Black-Box Opacity**: Autonomous agents that fail to log cryptographic step-by-step reasoning traces, citations, and input/output parameters cannot be audited or trusted in mission-critical environments.

### Target Users & Business Use Cases

OmniAgent AI is engineered for cross-functional enterprise departments:
- **Operations & Manufacturing**: Autonomous equipment inspection, defect classification from high-resolution imagery, automated maintenance dispatch, and operational logging.
- **Finance & Accounts Payable**: End-to-end invoice automation, purchase order reconciliation against PostgreSQL databases, anomaly detection, and approval-gated ERP entry posting.
- **IT & DevOps Support**: Ticket classification, automated root-cause analysis across log files and knowledge bases, and verified remediation execution.
- **Human Resources**: Policy inquiry resolution with strict vector grounding and document citations, employee onboarding checklist generation, and credential audit reviews.
- **Compliance & Legal**: Tamper-proof audit review, contract analysis, and strict tenant-isolated knowledge retrieval.

### Technical & Security Objectives

- **Hierarchical Cognitive Routing**: Dynamic decomposition of complex enterprise instructions into structured directed acyclic graphs (DAGs) executed by specialist agents via LangGraph.
- **Zero-Trust Multi-Tenancy**: Hardware and row-level multi-tenant isolation enforced through cryptographic tenant identifiers (`organization_id`) in all database tables, vector searches, and file storage prefixes.
- **Deterministic Action Gating**: Risk-classified execution boundaries (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) with HMAC-SHA256 cryptographically signed approvals and automatic expiration timers.
- **Verifiable RAG Grounding**: High-fidelity retrieval utilizing PostgreSQL 16 `pgvector` with 1536-dimensional embeddings, strict cosine distance ranking, and exact source citations.

---

# 2. Project Goals

OmniAgent AI was engineered to achieve rigorous operational, architectural, and security milestones:

1. **Cross-Modal Data Ingestion & Synthesis**: Ingest, parse, normalize, and query text, layout-aware PDFs, Word documents, spreadsheets, raster images, and SQL data stores within a unified conversational session.
2. **Autonomous Multi-Agent Orchestration**: Replace monolithic prompts with a modular swarm of specialized agents (Supervisor, Document, RAG, Database, Vision, Reasoning, Action) coordinated by LangGraph state machines.
3. **Provable Human-in-the-Loop Governance**: Guarantee that no state-changing action classified as `MEDIUM`, `HIGH`, or `CRITICAL` can execute without verified, authenticated human sign-off via HMAC SHA-256 signatures.
4. **Hardened SQL & Tool Sandboxing**: Provide zero-trust database interrogation allowing natural language querying of business tables while strictly rejecting DDL/DML mutations (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`) and preventing system catalog exploration.
5. **Immutable Compliance Auditing**: Generate SHA-256 hash-chained audit ledgers recording every user interaction, agent plan, tool invocation, human decision, and response latency.
6. **Production Enterprise Readiness**: Deliver a production-grade codebase with containerized microservices, comprehensive asynchronous FastAPI endpoints, a modern responsive React/TypeScript UI, and end-to-end automated testing pipelines.

---

# 3. Core Capabilities

OmniAgent AI incorporates the following verified capabilities implemented in the repository:

* **Natural Language Interaction**: Stateful, multi-turn conversational interface powered by FastAPI and React, supporting real-time streaming, contextual history retrieval, and execution tracking.
* **Document Understanding**: High-fidelity parsing of PDFs (tables and text blocks), DOCX, and TXT files, supporting automated classification, structured entity extraction, and executive summarization.
* **Retrieval-Augmented Generation (RAG)**: Enterprise knowledge search backed by PostgreSQL 16 and `pgvector`, performing 1536-dimensional vector similarity lookups, metadata filtering, and exact citation generation.
* **Database Agent & Text-to-SQL**: Semantic translation of natural language queries into read-only SQL statements against enterprise operational tables (`machines`, `orders`, `production_records`, `products`, `vendors`) with automated tenant filtering.
* **Computer Vision & Inspection**: Image ingestion, format and dimension validation, optical character recognition (OCR) via system engine abstraction, object detection hooks (YOLO/OpenCV interface), and visual anomaly detection.
* **Cross-Modal Reasoning**: Multi-step hypothesis evaluation, evidence synthesis across conflicting data sources, and resolution generation without exposing private chain-of-thought tokens.
* **Controlled Action Execution**: Enterprise actuation service supporting email dispatch, notification routing, support ticket creation, analytical report generation, and ERP posting adapters.
* **Workflow Automation**: Multi-step stateful workflow engine executing sequential DAG steps with trigger support (Manual, Database Event, Schedule, Webhook) and step-level approval pausing.
* **Human Approval Gating**: Interactive approval lifecycle featuring cryptographic payload hashing, expiration tracking, role-based sign-off, and state-preserving workflow suspension.
* **Audit Logging & Ledger**: SHA-256 hash-verified logging of system events, request IDs, IP addresses, actor identities, and full payload summaries.
* **Multi-Tenancy & RBAC**: Tenant isolation across all 27 database tables, reinforced by a 6-tier role hierarchy (`Owner`, `Admin`, `Supervisor`, `Operator`, `Auditor`, `Viewer`).

---

# 4. Current Implementation Status

The implementation status of each major subsystem within the repository is tracked below:

| Subsystem | Component | Implementation Status | Evidence / Source Code Location |
| :--- | :--- | :---: | :--- |
| **Frontend** | React 18 SPA + Vite + Tailwind | ✅ Implemented | `frontend/src/` (20 pages, 10+ services, components) |
| **Backend Core** | FastAPI + Uvicorn + Middleware | ✅ Implemented | `backend/app/main.py`, `backend/app/core/` |
| **Database** | PostgreSQL 16 + pgvector (27 tables) | ✅ Implemented | `backend/app/models/`, `backend/app/db/` |
| **Migrations** | Alembic Environment & Versioning | ✅ Implemented | `backend/alembic.ini`, `backend/migrations/` |
| **Authentication** | JWT (HS256) + bcrypt + OAuth2 | ✅ Implemented | `backend/app/core/security.py`, `backend/app/api/v1/auth.py` |
| **RBAC** | 6 Roles + Granular Permissions | ✅ Implemented | `backend/app/models/role.py`, `backend/app/dependencies/permissions.py` |
| **Multi-Tenancy** | Shared Database, Row-Level Isolation | ✅ Implemented | `organization_id` column on all 27 models, repository filters |
| **Supervisor Agent** | Intent Routing & Task Decomposition | ✅ Implemented | `agents/supervisor/`, `backend/app/api/v1/agents.py` |
| **Document Agent** | PDF/DOCX/TXT Ingestion & Parsing | ✅ Implemented | `agents/document/`, `backend/app/services/document_service.py` |
| **RAG Agent** | pgvector Vector Search & Citations | ✅ Implemented | `agents/rag/`, `backend/app/services/rag_service.py` |
| **Database Agent** | Text-to-SQL + Security Validator | ✅ Implemented | `agents/database/`, `backend/app/services/database_service.py` |
| **Vision Agent** | OCR, Anomaly Detection & Untrusted Delimiters | ✅ Implemented | `agents/vision/`, `backend/app/services/vision_service.py` |
| **Reasoning Agent** | Evidence Synthesis & Conflict Detection | ✅ Implemented | `agents/reasoning/`, `backend/app/services/reasoning_service.py` |
| **Action Agent** | Email, Tickets, Reports, Notifications | ✅ Implemented | `agents/action/`, `backend/app/services/action_service.py` |
| **Orchestrator** | LangGraph StateGraph Execution Loop | ✅ Implemented | `backend/app/orchestration/graph.py`, `backend/app/orchestration/nodes.py` |
| **Automation Engine** | StepExecutor, WorkflowEngine, State | ✅ Implemented | `automation/engine/`, `automation/workflows/` |
| **HITL Approvals** | HMAC Signatures, Hash Binding, Expiry | ✅ Implemented | `backend/app/models/approval.py`, `agents/action/approval.py` |
| **Multimodal Audio** | Audio Processing & Transcription | 🟡 Partially Implemented | `multimodal/audio/` (Mock/Scaffolding provider active) |
| **Multimodal Video** | Video Analysis & Keyframe Extraction | 🟡 Partially Implemented | `multimodal/video/` (Mock/Scaffolding analyzer active) |
| **Vector Reranking** | Cross-Encoder / Reciprocal Rank Fusion | 🟡 Partially Implemented | `backend/app/services/rag/retrieval/reranking.py` (Pass-through top_k) |
| **Docker Compose** | 6 Containers (Postgres, Redis, MinIO, Backend, Worker, Frontend) | ✅ Implemented | `docker-compose.yml`, `infrastructure/docker/` |
| **CI/CD Pipelines** | GitHub Actions (Lint, Unit, Integration, Frontend) | ✅ Implemented | `.github/workflows/` (3 active workflows) |
| **Cloud Deploy** | AWS ECS, Vercel, Render configurations | ✅ Implemented | `infrastructure/cloud/`, `vercel.json` |

---

# 5. Complete Project Structure

The verified filesystem hierarchy of the repository is structured as follows:

```text
OmniAgent-AI/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── workflows/
│       ├── backend-tests.yml
│       ├── ci.yml
│       └── frontend-build.yml
├── agents/
│   ├── action/              # Enterprise actuation, risk gating, execution policies
│   ├── database/            # Text-to-SQL generation, schema registry, SQL guardrails
│   ├── document/            # PDF, DOCX, TXT parsers, classification, summarization
│   ├── evaluation/          # Trajectory evaluators, faithfulness metrics
│   ├── graph/               # High-level LangGraph agent graph definitions
│   ├── memory/              # Short-term, working, and long-term memory adapters
│   ├── prompts/             # System prompts for supervisor, rag, vision, action
│   ├── rag/                 # Vector retrieval, semantic search, citation generator
│   ├── reasoning/           # Grounded multi-step reasoning, cross-modal reconciliation
│   ├── supervisor/          # Master cognitive router, intent classifier, DAG planner
│   └── vision/              # Image validation, OCR abstraction, visual inspection
├── automation/
│   ├── actions/             # Workflow action handlers (email, report, ticket, db)
│   ├── approvals/           # Workflow risk evaluation and approval policies
│   ├── conditions/          # Condition evaluation engine and rule operators
│   ├── engine/              # Core workflow runner, step executor, state tracking
│   ├── triggers/            # Workflow triggers (manual, schedule, webhook, db event)
│   └── workflows/           # Pre-built templates (invoice, manufacturing, customer support)
├── backend/
│   ├── alembic.ini          # Database migration configuration
│   ├── app/
│   │   ├── api/             # FastAPI routers and v1 endpoints
│   │   ├── core/            # Configuration, logging, security, exceptions, middleware
│   │   ├── db/              # SQLAlchemy session setup, declarative Base
│   │   ├── dependencies/    # FastAPI dependency injection (auth, permissions, db)
│   │   ├── models/          # 27 SQLAlchemy ORM database models
│   │   ├── orchestration/   # LangGraph orchestration state machine, nodes, events
│   │   ├── repositories/    # Encapsulated database access repositories
│   │   ├── schemas/         # Pydantic v2 validation and transfer schemas
│   │   ├── services/        # Application business logic services
│   │   ├── utils/           # File, pagination, and string validation helpers
│   │   └── workers/         # Celery background workers for indexing and workflows
│   ├── migrations/          # Alembic migration scripts and env.py
│   └── requirements.txt     # Python backend dependencies
├── database/
│   ├── schema/              # SQL schema DDL and ERD documentation
│   └── seeds/               # Baseline enterprise seed data
├── docs/                    # Architecture and module documentation
├── frontend/
│   ├── package.json         # Node.js dependencies and build scripts
│   ├── vite.config.ts       # Vite bundler configuration
│   ├── tailwind.config.js   # Tailwind CSS design system configuration
│   └── src/
│       ├── components/      # Reusable React components (approvals, chat, citations)
│       ├── contexts/        # React authentication context
│       ├── pages/           # 20 application page views
│       ├── services/        # Axios API client integrations
│       ├── store/           # Zustand client state stores
│       └── types/           # TypeScript interface definitions
├── infrastructure/
│   ├── cloud/               # AWS ECS task definitions and Vercel configs
│   ├── docker/              # Dockerfiles for backend, worker, and frontend
│   ├── monitoring/          # Prometheus configuration and Grafana dashboards
│   ├── nginx/               # Production Nginx reverse proxy configuration
│   ├── postgres/            # Database initialization SQL scripts
│   ├── redis/               # Redis server configuration
│   └── scripts/             # Automated deployment and backup bash scripts
├── md/
│   └── OMNIAGENT_AI_COMPLETE_DOCUMENTATION.md # Single source of truth documentation
├── multimodal/
│   ├── audio/               # Audio transcription and processing
│   ├── documents/           # DOCX and PPTX extraction
│   ├── image/               # Image transformation, resizing, classification
│   ├── ocr/                 # Optical character recognition wrappers
│   ├── pdf/                 # Layout-aware PDF and table extractors
│   ├── structured_data/     # CSV and Excel data parsers
│   ├── text/                # Text normalization and token counters
│   └── video/               # Video analysis and keyframe extraction
├── scripts/                 # PowerShell and bash utility scripts for setup and dev
├── storage/                 # Local filesystem storage fallback for documents & images
├── tests/
│   ├── e2e/                 # End-to-end full pipeline integration tests
│   ├── evaluation/          # RAG, OCR, and trajectory metric evaluations
│   ├── integration/         # API endpoint and database integration tests
│   ├── security/            # Prompt injection, SQL safety, RBAC security tests
│   └── unit/                # Unit tests for agents, automation, and backend
├── docker-compose.yml       # Multi-container local orchestration configuration
├── Makefile                 # Developer CLI task automation
├── README.md                # Repository root overview
└── SECURITY.md              # Security policies and vulnerability reporting
```

### Directory Responsibilities

- `backend/app/models/`: Defines the declarative database schema across 27 tables. Serves as the ultimate source of truth for all enterprise entities.
- `backend/app/orchestration/`: Houses the master LangGraph multi-agent cognitive engine, execution limits, event recorder, and state machine transitions.
- `agents/`: Independent specialist modules encapsulating prompt templates, domain schemas, guardrails, and deterministic tool callers.
- `automation/`: Autonomous execution engine managing scheduled, manual, and event-driven business workflows across discrete task steps.
- `multimodal/`: Extraction pipelines normalizing heterogeneous inputs into standardized text, image, and structured representations.
- `tools/`: Deterministic connectors interacting with enterprise boundary systems (PostgreSQL, SMTP, ERPs, Jira, MinIO).
- `frontend/`: Single-page React application delivering operational dashboards, visual agent execution traces, citation inspectors, and approval interfaces.

---

# 6. System Architecture

OmniAgent AI is architected as an asynchronous, layered, modular monolith with clean domain boundaries, designed for horizontal extraction into microservices if needed:

```mermaid
flowchart TD
    subgraph Client["Presentation Layer (Client)"]
        User(["Enterprise User / Browser"])
        SPA["React 18 + Vite SPA<br/>(Tailwind CSS, Zustand, Lucide)"]
        User <--> SPA
    end

    subgraph Gateway["Edge & Gateway Layer"]
        Nginx["Nginx Reverse Proxy<br/>(Port 80 / Port 3000)"]
        SPA <-->|HTTP / REST| Nginx
    end

    subgraph API["Application & API Layer"]
        FastAPI["FastAPI 0.111 Application<br/>(Port 8000)"]
        Middleware["RequestTrace & CORS Middleware"]
        AuthFilter["OAuth2 / JWT RBAC Guard"]
        Nginx <-->|Proxy Pass /api/| FastAPI
        FastAPI --> Middleware --> AuthFilter
    end

    subgraph Cognitive["Cognitive Orchestration Layer"]
        Orchestrator["Unified LangGraph Orchestrator"]
        Supervisor["Supervisor Agent<br/>(Intent Routing & Task DAG)"]
        AuthFilter --> Orchestrator
        Orchestrator --> Supervisor
        
        Supervisor --> DocAgent["Document Agent"]
        Supervisor --> RAGAgent["RAG Agent"]
        Supervisor --> DBAgent["Database Agent"]
        Supervisor --> VisAgent["Vision Agent"]
        Supervisor --> ReasonAgent["Reasoning Agent"]
        Supervisor --> ActAgent["Action Agent"]
    end

    subgraph Safety["Governance & Safety Layer"]
        HITL{"Human-in-the-Loop Gate<br/>Risk >= MEDIUM?"}
        HMAC["HMAC SHA-256 Signatures<br/>& Expiration Engine"]
        AuditLedger["SHA-256 Chained<br/>Audit Ledger"]
        
        ActAgent --> HITL
        HITL -->|Yes| HMAC -->|Approved| ToolExec["Tool / Worker Dispatch"]
        HITL -->|No| ToolExec
        ToolExec --> AuditLedger
    end

    subgraph Data["Persistence & Infrastructure Layer"]
        Postgres[("PostgreSQL 16 Database<br/>(Relational Business Tables)")]
        VectorStore[("pgvector Extension<br/>(1536-dim Document Chunks)")]
        RedisStore[("Redis 7 Cache<br/>& Celery Broker")]
        ObjectStore[("MinIO / AWS S3<br/>(Document & Image Storage)")]
        
        DBAgent <-->|Read-Only SELECT| Postgres
        RAGAgent <-->|Cosine Search| VectorStore
        ToolExec <--> RedisStore
        DocAgent <--> ObjectStore
        VisAgent <--> ObjectStore
        AuditLedger --> Postgres
    end
```

### Architectural Data Flow

1. The client browser communicates over HTTPS to Nginx, which serves static assets and reverse-proxies `/api/v1` routes to the FastAPI application.
2. The FastAPI `RequestTraceMiddleware` assigns a cryptographically unique `X-Request-ID` and records total execution latency.
3. JWT tokens are verified by `get_current_user`, resolving tenant context (`organization_id`) and user roles.
4. Requests entering the unified chat endpoint (`/api/v1/chat`) invoke the `Orchestrator`, which initiates a LangGraph state graph.
5. The `Supervisor Agent` inspects message intent, extracts multimodal attachments, and dynamically routes tasks to specialized worker agents.
6. Worker agents query underlying stores (PostgreSQL via Database Agent, pgvector via RAG Agent, MinIO via Document/Vision Agents).
7. If an actuation step is planned, the `Action Agent` performs risk classification. Operations rated `MEDIUM` or `HIGH` are halted at the approval gate, generating an approval record and notifying authorized managers.
8. Once verified or approved, actions execute through the tool registry, generate HMAC SHA-256 audit log entries, and synthesize grounded responses.

---

# 7. Technology Stack

The entire technology stack utilized across the repository is detailed in the table below:

| Architectural Layer | Technology | Version | Purpose in OmniAgent AI | Implementation Status |
| :--- | :--- | :--- | :--- | :---: |
| **Frontend Framework** | React | `18.3.1` | Core declarative component UI | ✅ Implemented |
| **Frontend Language** | TypeScript | `5.4.5` | Type-safe client codebase | ✅ Implemented |
| **Build Tooling** | Vite | `5.2.10` | Fast HMR and optimized production bundling | ✅ Implemented |
| **Styling** | Tailwind CSS | `3.4.3` | Utility-first responsive design system | ✅ Implemented |
| **Client State** | Zustand | `4.5.2` | Minimalist client authentication store | ✅ Implemented |
| **Server State** | TanStack Query | `5.32.0` | Asynchronous data fetching and caching | ✅ Implemented |
| **Client Validation**| Zod | `3.23.8` | Client schema parsing and form validation | ✅ Implemented |
| **Icons** | Lucide React | `0.378.0` | Enterprise dashboard iconography | ✅ Implemented |
| **Backend Framework** | FastAPI | `0.111.0` | High-performance asynchronous REST API | ✅ Implemented |
| **Backend Language** | Python | `3.11` | Primary backend execution runtime | ✅ Implemented |
| **Validation / DTO** | Pydantic | `2.7.0` | Data serialization, request validation | ✅ Implemented |
| **Settings** | Pydantic Settings | `2.2.1` | Type-safe environment variable parsing | ✅ Implemented |
| **Async ORM** | SQLAlchemy | `2.0.29` | Asynchronous database object-relational mapping | ✅ Implemented |
| **DB Driver** | asyncpg | `0.29.0` | High-throughput asynchronous PostgreSQL driver | ✅ Implemented |
| **Migrations** | Alembic | `1.13.1` | Schema versioning and migration automation | ✅ Implemented |
| **Database** | PostgreSQL | `16.0` | Primary ACID relational database | ✅ Implemented |
| **Vector Engine** | pgvector | `0.7.0` (pg16) | Native 1536-dim vector similarity search | ✅ Implemented |
| **Distributed Queue**| Redis / Celery | `7-alpine` / `5.3.6` | Task queuing, caching, asynchronous workers | ✅ Implemented |
| **Object Storage** | MinIO / Boto3 | `RELEASE` / `1.34` | S3-compatible document and image persistence | ✅ Implemented |
| **Agent Framework** | LangGraph | `0.0.40` | Stateful cyclical multi-agent graph coordinator | ✅ Implemented |
| **AI LLM Core** | OpenAI GPT-4o | API | Primary cognitive reasoning and instruction model| ✅ Implemented |
| **Embeddings** | text-embedding-3-large | API | 1536-dimensional semantic text vectors | ✅ Implemented |
| **Logging** | Structlog | `24.1.0` | Structured JSON log generation with contextvars | ✅ Implemented |
| **Auth Cryptography**| python-jose / bcrypt | `3.3.0` / `4.0.1` | JWT signing, verification, password hashing | ✅ Implemented |
| **Reverse Proxy** | Nginx | `alpine` | Static file delivery and API proxying | ✅ Implemented |
| **Testing** | Pytest / pytest-asyncio| `8.1.1` / `0.23.6`| Asynchronous unit, integration, and security tests | ✅ Implemented |

---

# 8. Frontend Architecture

The frontend application (`frontend/`) is an enterprise-grade Single Page Application (SPA) built with React 18, TypeScript, and Vite.

### Directory Structure & Organization

```text
frontend/src/
├── App.tsx                     # Top-level routing and layout shell
├── main.tsx                    # React DOM root entry point
├── index.css                   # Tailwind CSS root directives
├── components/
│   ├── agents/
│   │   └── EvidenceList.tsx    # Displays grounded agent evidence cards
│   ├── approvals/
│   │   └── ApprovalCard.tsx    # Interactive human-in-the-loop sign-off card
│   ├── citations/
│   │   └── CitationsList.tsx   # Verified document citation drawer
│   ├── execution/
│   │   └── AgentActivitySection.tsx # Real-time agent execution step timeline
│   ├── layout/
│   │   └── AppLayout.tsx       # Sidebar navigation, header, user status
│   ├── ui/
│   │   ├── Button.tsx          # Reusable styled button variants
│   │   └── Card.tsx            # Styled card container
│   └── workflows/
│       ├── WorkflowEditor.tsx  # Interactive workflow DAG editor
│       ├── WorkflowList.tsx    # Workflow templates and definitions
│       └── WorkflowRunHistory.tsx # Execution run history timeline
├── config/
│   └── env.ts                  # Environment configuration (API URL)
├── constants/
│   └── routes.ts               # Static route definitions
├── contexts/
│   └── AuthContext.tsx         # User authentication provider
├── hooks/
│   └── useAuth.ts              # Authentication state hook
├── pages/                      # 20 Enterprise Application Pages
│   ├── Admin/                  # Tenant user and role administration
│   ├── AgentRuns/              # Historical agent run ledger
│   ├── Agents/                 # Specialist agent capability overview
│   ├── Analytics/              # Token costs, latencies, execution metrics
│   ├── Approvals/              # Pending action approval queue
│   ├── Chat/                   # Unified multi-agent interactive interface
│   ├── Dashboard/              # High-level operational health and counters
│   ├── Documents/              # Document management and ingestion
│   ├── ImageAnalysis/          # Computer vision inspection interface
│   ├── Integrations/           # ERP, SMTP, Slack, Web connectors
│   ├── KnowledgeBase/          # Vector search query explorer
│   ├── Landing/                # Public product landing page
│   ├── Login/                  # Authentication login portal
│   ├── Notifications/          # Operational alerts and messages
│   ├── Register/               # Tenant user registration portal
│   ├── Settings/               # Profile, security, and API configurations
│   ├── Tasks/                  # Operational tasks board
│   ├── Video/                  # Video stream analysis page
│   ├── Voice/                  # Voice dictation and transcription page
│   └── Workflows/              # Enterprise automation workflow management
├── services/
│   ├── api/
│   │   └── client.ts           # Axios HTTP client with JWT interceptors
│   ├── agents/agentService.ts  # Specialist agent execution APIs
│   ├── analytics/analyticsService.ts # Platform metrics APIs
│   ├── approvals/approvalService.ts  # Approve/Reject action APIs
│   ├── auth/authService.ts     # Login, registration, token refresh
│   ├── chat/chatService.ts     # Unified chat conversation APIs
│   ├── documents/documentService.ts # Document upload and indexing APIs
│   ├── vision/visionService.ts # Image analysis and OCR APIs
│   └── workflows/workflowService.ts # Automation workflow execution APIs
├── store/
│   └── authStore.ts            # Zustand persistent authentication store
└── utils/
    ├── cn.ts                   # ClassName merger (clsx + tailwind-merge)
    ├── formatters.ts           # Date, latency, currency formatters
    ├── token.ts                # LocalStorage JWT token management
    └── validation.ts           # Input validation helpers
```

### State Management & Axios Interceptors

Client state is partitioned into two distinct paradigms:
1. **Global Auth State (`src/store/authStore.ts`)**: Implemented via Zustand with local storage persistence. Stores `token`, `refreshToken`, and the deserialized `user` profile (`id`, `email`, `role`, `organization_id`).
2. **Server State (`@tanstack/react-query`)**: Handles caching, automatic background invalidation, and optimistic UI updates for chat threads, approvals, documents, and workflow runs.

The Axios HTTP client (`src/services/api/client.ts`) attaches an authorization interceptor to every outgoing request:
```typescript
client.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```
When receiving a 401 response, the client intercepts the error, clears expired authentication credentials, and routes the user to `/login`.

---

# 9. Backend Architecture

The backend (`backend/app/`) is built on FastAPI 0.111.0, leveraging Python 3.11 asynchronous programming constructs (`async`/`await`), Pydantic v2 schemas, and SQLAlchemy 2.0 async ORM.

### Application Startup & Lifecycle

The application lifecycle is defined in `backend/app/main.py`:
1. **Logging Initialization (`setup_logging()`)**: Configures `structlog` to emit structured JSON logs in production (`DEBUG=False`) or human-readable colorized terminal output in development.
2. **Middleware Registration**:
   - `RequestTraceMiddleware`: Inspects or injects an `X-Request-ID` UUID, attaches timing metrics, and records structured execution logs upon completion.
   - `CORSMiddleware`: Restricts cross-origin requests to allowlisted client origins defined in `settings.ALLOWED_ORIGINS`.
3. **Exception Handlers**: Traps `BaseAppException` derivatives, formatting standard JSON responses with status code 400 and full diagnostic payloads.
4. **Router Mounting**: Registers `api_router` under the global prefix `/api/v1`.

### Dependency Injection Pipeline

FastAPI dependencies enforce modular security and database boundaries:
- `get_db_session`: Yields an `AsyncSession` from the connection pool, handling rollback on failure and automatic commit on success.
- `get_current_user`: Extracts the Bearer token, verifies its signature and expiration using `python-jose`, and loads the active `User` record scoped to the organization.
- `require_role(allowed_roles: list[str])`: Verifies that the authenticated user possesses an authorized system role before allowing endpoint execution.

### Service & Repository Layers

To ensure separation of concerns, the backend strictly separates business logic from database interactions:
- **Repositories (`backend/app/repositories/`)**: Encapsulate SQL queries via SQLAlchemy. Examples: `UserRepository`, `DocumentRepository`, `ConversationRepository`, `WorkflowRepository`, `AuditRepository`, `AgentRepository`. All repository methods require an explicit `organization_id` to guarantee tenant isolation.
- **Services (`backend/app/services/`)**: Contain domain orchestration logic, coordinating repositories, external APIs, and agents. Examples: `ChatService`, `ActionService`, `DocumentService`, `RAGService`, `DatabaseService`, `VisionService`, `ReasoningService`, `WorkflowService`, `AuditService`.

---

# 10. Database Architecture

OmniAgent AI uses PostgreSQL 16 with the `pgvector` extension for combined relational and vector storage.

### Multi-Tenant Segregation Strategy

The platform employs a **Shared Database, Row-Level Isolation** multi-tenancy model:
- Every tenant belongs to an `Organization`.
- All tenant-owned tables maintain an indexed `organization_id` foreign key referencing `organizations(id) ON DELETE CASCADE`.
- Database repositories and query builders automatically inject `WHERE organization_id = :org_id` clauses into all queries.
- In-memory data structures and RAG vector searches strictly isolate candidate chunks by `organization_id`.

### Connection Pooling & Async Engine

Database connections are managed via SQLAlchemy's `create_async_engine` using the `asyncpg` driver:
```python
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)
```
For Alembic migrations, `NullPool` is configured to ensure schema operations execute safely without holding open stale pooled connections.

---

# 11. Database Schema

The database schema is defined across 27 SQLAlchemy models in `backend/app/models/`. Every model inherits from `Base` (`backend/app/db/base.py`).

### Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    organizations ||--o{ departments : contains
    organizations ||--o{ users : employs
    organizations ||--o{ roles : defines
    organizations ||--o{ documents : owns
    organizations ||--o{ workflows : configures
    organizations ||--o{ audit_logs : generates
    organizations ||--o{ integrations : configures
    organizations ||--o{ machines : operates
    organizations ||--o{ orders : processes
    organizations ||--o{ products : catalogs
    organizations ||--o{ vendors : contracts

    roles ||--o{ role_permissions : assigns
    permissions ||--o{ role_permissions : granted_to
    roles ||--o{ users : assigned_to
    departments ||--o{ users : assigns_to
    departments ||--o{ machines : houses

    users ||--o{ conversations : initiates
    users ||--o{ documents : uploads
    users ||--o{ approvals : decides
    users ||--o{ notifications : receives
    users ||--o{ workflows : creates
    users ||--o{ actions : requests

    documents ||--o{ document_chunks : chunked_into
    conversations ||--o{ messages : contains
    conversations ||--o{ agent_runs : executes

    agent_runs ||--o{ tool_calls : invokes
    agent_runs ||--o| approvals : triggers

    workflows ||--o{ workflow_runs : executes
    workflow_runs ||--o| approvals : pauses_for

    actions ||--o{ action_approvals : requires
    actions ||--o{ action_audit_logs : logs

    machines ||--o{ production_records : generates
    machines ||--o{ maintenance_requests : logs
```

### Complete Inventory of All 27 Database Tables

#### 1. `organizations`
- **Purpose**: Master tenant entities for multi-tenant isolation.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `name` (VARCHAR(255), NOT NULL)
  - `slug` (VARCHAR(100), NOT NULL, UNIQUE)
  - `is_active` (BOOLEAN, NOT NULL, default True)
  - `created_at` (DATETIME, NOT NULL)
  - `updated_at` (DATETIME, NOT NULL)
- **Relationships**: Owns all tenant resources via CASCADE.

#### 2. `departments`
- **Purpose**: Organizational subdivisions (e.g. IT, Finance, HR).
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `name` (VARCHAR(150), NOT NULL)
  - `code` (VARCHAR(50), NOT NULL)
  - `created_at` (DATETIME, NOT NULL)

#### 3. `users`
- **Purpose**: Authenticated user accounts with role assignments.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `department_id` (UUID, FK -> departments.id, NULL)
  - `email` (VARCHAR(255), NOT NULL, UNIQUE per org)
  - `hashed_password` (VARCHAR(255), NOT NULL)
  - `full_name` (VARCHAR(255), NOT NULL)
  - `role_id` (UUID, FK -> roles.id, NOT NULL)
  - `is_active` (BOOLEAN, NOT NULL, default True)
  - `is_verified` (BOOLEAN, NOT NULL, default False)
  - `created_at` (DATETIME, NOT NULL)
  - `updated_at` (DATETIME, NOT NULL)

#### 4. `roles`
- **Purpose**: System and organization role definitions.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NULL for system roles)
  - `name` (VARCHAR(100), NOT NULL)
  - `description` (VARCHAR, NULL)
  - `is_system_role` (BOOLEAN, NOT NULL, default False)
  - `created_at` (DATETIME, NOT NULL)
- **Relationships**: `permissions` via `role_permissions`.

#### 5. `permissions`
- **Purpose**: Granular system capability definitions.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `name` (VARCHAR(100), NOT NULL, UNIQUE)
  - `description` (VARCHAR, NULL)
  - `category` (VARCHAR(50), NOT NULL)

#### 6. `role_permissions`
- **Purpose**: Many-to-many junction table binding roles to permissions.
- **Columns**:
  - `role_id` (UUID, PK, FK -> roles.id, NOT NULL)
  - `permission_id` (UUID, PK, FK -> permissions.id, NOT NULL)

#### 7. `documents`
- **Purpose**: Uploaded files and metadata.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `uploaded_by` (UUID, FK -> users.id, NULL)
  - `file_name` (VARCHAR(255), NOT NULL)
  - `file_path` (TEXT, NOT NULL)
  - `file_type` (VARCHAR(100), NOT NULL)
  - `file_size_bytes` (BIGINT, NOT NULL)
  - `checksum_sha256` (VARCHAR(64), NOT NULL)
  - `processing_status` (VARCHAR(50), NOT NULL, default "PENDING")
  - `metadata` (JSONB, NOT NULL, default {})
  - `created_at` (DATETIME, NOT NULL)
  - `updated_at` (DATETIME, NOT NULL)

#### 8. `document_chunks`
- **Purpose**: Text chunks and 1536-dimensional vector embeddings for RAG.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `document_id` (UUID, FK -> documents.id, NOT NULL)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `chunk_index` (INTEGER, NOT NULL)
  - `content` (TEXT, NOT NULL)
  - `token_count` (INTEGER, NOT NULL)
  - `embedding` (VECTOR(1536), NULL)
  - `metadata` (JSONB, NOT NULL, default {})
  - `created_at` (DATETIME, NOT NULL)

#### 9. `conversations`
- **Purpose**: Multi-turn chat sessions.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `user_id` (UUID, FK -> users.id, NOT NULL)
  - `title` (VARCHAR(255), NOT NULL)
  - `agent_type` (VARCHAR(50), NOT NULL)
  - `created_at` (DATETIME, NOT NULL)
  - `updated_at` (DATETIME, NOT NULL)

#### 10. `messages`
- **Purpose**: Individual messages within a conversation.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `conversation_id` (UUID, FK -> conversations.id, NOT NULL)
  - `sender_type` (VARCHAR(50), NOT NULL)
  - `content` (TEXT, NOT NULL)
  - `citations` (JSONB, NULL, default [])
  - `metadata` (JSONB, NULL, default {})
  - `created_at` (DATETIME, NOT NULL)

#### 11. `agent_runs`
- **Purpose**: Trace records of specialist agent executions.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `conversation_id` (UUID, FK -> conversations.id, NULL)
  - `user_id` (UUID, FK -> users.id, NULL)
  - `agent_name` (VARCHAR(100), NOT NULL)
  - `task_description` (TEXT, NOT NULL)
  - `status` (VARCHAR(50), NOT NULL)
  - `started_at` (DATETIME, NOT NULL)
  - `completed_at` (DATETIME, NULL)
  - `latency_ms` (INTEGER, NULL)
  - `total_tokens` (INTEGER, NOT NULL, default 0)
  - `cost_usd` (NUMERIC(10, 6), NOT NULL, default 0.0)
  - `error_message` (TEXT, NULL)

#### 12. `tool_calls`
- **Purpose**: Record of tool invocations performed by agents.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `agent_run_id` (UUID, FK -> agent_runs.id, NOT NULL)
  - `tool_name` (VARCHAR(100), NOT NULL)
  - `input_parameters` (JSONB, NOT NULL)
  - `output_result` (JSONB, NULL)
  - `risk_level` (VARCHAR(20), NOT NULL, default "LOW")
  - `requires_approval` (BOOLEAN, NOT NULL, default False)
  - `approval_id` (UUID, NULL)
  - `status` (VARCHAR(50), NOT NULL, default "PENDING")
  - `executed_at` (DATETIME, NULL)
  - `execution_latency_ms` (INTEGER, NULL)

#### 13. `approvals`
- **Purpose**: Orchestrator and agent approval requests.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `agent_run_id` (UUID, FK -> agent_runs.id, NULL)
  - `workflow_run_id` (UUID, FK -> workflow_runs.id, NULL)
  - `action_type` (VARCHAR(100), NOT NULL)
  - `risk_level` (VARCHAR(20), NOT NULL)
  - `action_payload` (JSONB, NOT NULL)
  - `reason` (TEXT, NOT NULL)
  - `status` (VARCHAR(50), NOT NULL, default "PENDING")
  - `requested_by` (UUID, FK -> users.id, NULL)
  - `decided_by` (UUID, FK -> users.id, NULL)
  - `decision_reason` (TEXT, NULL)
  - `decided_at` (DATETIME, NULL)
  - `signature_hmac` (VARCHAR(128), NULL)
  - `created_at` (DATETIME, NOT NULL)

#### 14. `audit_logs`
- **Purpose**: Immutable platform audit trail.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `user_id` (UUID, FK -> users.id, NULL)
  - `event_type` (VARCHAR(100), NOT NULL)
  - `resource_type` (VARCHAR(100), NOT NULL)
  - `resource_id` (VARCHAR(100), NOT NULL)
  - `ip_address` (VARCHAR(45), NULL)
  - `details` (JSONB, NOT NULL)
  - `entry_hash` (VARCHAR(64), NOT NULL)
  - `created_at` (DATETIME, NOT NULL)

#### 15. `workflows`
- **Purpose**: Workflow definitions and graph configuration.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `created_by` (UUID, FK -> users.id, NULL)
  - `name` (VARCHAR(255), NOT NULL)
  - `description` (TEXT, NULL)
  - `trigger_type` (VARCHAR(50), NOT NULL)
  - `trigger_config` (JSONB, NOT NULL, default {})
  - `graph_definition` (JSONB, NOT NULL)
  - `is_active` (BOOLEAN, NOT NULL, default True)
  - `created_at` (DATETIME, NOT NULL)
  - `updated_at` (DATETIME, NOT NULL)

#### 16. `workflow_runs`
- **Purpose**: Executed instances of a workflow.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `workflow_id` (UUID, FK -> workflows.id, NOT NULL)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `status` (VARCHAR(50), NOT NULL, default "PENDING")
  - `current_step` (VARCHAR(100), NULL, default "1")
  - `input_payload` (JSONB, NOT NULL, default {})
  - `output_payload` (JSONB, NULL)
  - `started_at` (DATETIME, NOT NULL)
  - `finished_at` (DATETIME, NULL)
  - `error_details` (TEXT, NULL)

#### 17. `actions`
- **Purpose**: Action Agent execution requests and results.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `requested_by` (UUID, FK -> users.id, NULL)
  - `action_type` (VARCHAR(100), NOT NULL)
  - `risk_level` (VARCHAR(20), NOT NULL)
  - `status` (VARCHAR(50), NOT NULL)
  - `idempotency_key` (VARCHAR(128), NULL)
  - `input_hash` (VARCHAR(64), NULL)
  - `input_payload` (JSONB, NOT NULL)
  - `result_payload` (JSONB, NULL)
  - `error_message` (TEXT, NULL)
  - `external_reference` (VARCHAR(255), NULL)
  - `verified` (BOOLEAN, NOT NULL, default False)
  - `created_at` (DATETIME, NOT NULL)
  - `updated_at` (DATETIME, NOT NULL)
  - `completed_at` (DATETIME, NULL)

#### 18. `action_approvals`
- **Purpose**: Gated approvals specific to Action Agent invocations.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `action_id` (UUID, FK -> actions.id, NOT NULL)
  - `requested_by` (UUID, FK -> users.id, NULL)
  - `action_type` (VARCHAR(100), NOT NULL)
  - `payload_summary` (TEXT, NOT NULL)
  - `risk_level` (VARCHAR(20), NOT NULL)
  - `status` (VARCHAR(50), NOT NULL)
  - `payload_hash` (VARCHAR(64), NOT NULL)
  - `approved_by` (UUID, FK -> users.id, NULL)
  - `approved_at` (DATETIME, NULL)
  - `rejected_at` (DATETIME, NULL)
  - `expires_at` (DATETIME, NOT NULL)
  - `decision_reason` (TEXT, NULL)
  - `signature_hmac` (VARCHAR(128), NULL)
  - `created_at` (DATETIME, NOT NULL)
  - `updated_at` (DATETIME, NOT NULL)

#### 19. `action_audit_logs`
- **Purpose**: Detailed audit records of action lifecycle transitions.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `user_id` (UUID, FK -> users.id, NULL)
  - `action_id` (VARCHAR(100), NOT NULL)
  - `action_type` (VARCHAR(100), NOT NULL)
  - `event_type` (VARCHAR(100), NOT NULL)
  - `status` (VARCHAR(50), NOT NULL)
  - `risk_level` (VARCHAR(20), NOT NULL)
  - `request_id` (VARCHAR(100), NULL)
  - `approval_id` (VARCHAR(100), NULL)
  - `external_reference` (VARCHAR(255), NULL)
  - `details` (JSONB, NOT NULL)
  - `entry_hash` (VARCHAR(64), NOT NULL)
  - `created_at` (DATETIME, NOT NULL)

#### 20. `machines`
- **Purpose**: Manufacturing operational equipment records.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `name` (VARCHAR(150), NOT NULL)
  - `machine_code` (VARCHAR(50), NOT NULL)
  - `department_id` (UUID, FK -> departments.id, NULL)
  - `status` (VARCHAR(50), NOT NULL, default "OPERATIONAL")
  - `failure_count` (INTEGER, NOT NULL, default 0)
  - `created_at` (DATETIME, NOT NULL)
  - `updated_at` (DATETIME, NOT NULL)

#### 21. `production_records`
- **Purpose**: Manufacturing batch outputs and defect tracking.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `machine_id` (UUID, FK -> machines.id, NULL)
  - `batch_number` (VARCHAR(100), NOT NULL)
  - `status` (VARCHAR(50), NOT NULL, default "PASSED")
  - `defect_count` (INTEGER, NOT NULL, default 0)
  - `production_time_hours` (NUMERIC(10, 2), NOT NULL, default 0.0)
  - `notes` (TEXT, NULL)
  - `created_at` (DATETIME, NOT NULL)

#### 22. `orders`
- **Purpose**: Enterprise sales and procurement orders.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `order_number` (VARCHAR(100), NOT NULL)
  - `customer_name` (VARCHAR(255), NOT NULL)
  - `status` (VARCHAR(50), NOT NULL, default "PENDING")
  - `total_amount` (NUMERIC(12, 2), NOT NULL, default 0.0)
  - `created_at` (DATETIME, NOT NULL)
  - `updated_at` (DATETIME, NOT NULL)

#### 23. `products`
- **Purpose**: Enterprise catalog items, SKU, and pricing.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `name` (VARCHAR(255), NOT NULL)
  - `sku` (VARCHAR(100), NOT NULL)
  - `category` (VARCHAR(100), NOT NULL)
  - `price` (NUMERIC(10, 2), NOT NULL, default 0.0)
  - `usage_count` (INTEGER, NOT NULL, default 0)
  - `is_active` (BOOLEAN, NOT NULL, default True)
  - `created_at` (DATETIME, NOT NULL)

#### 24. `vendors`
- **Purpose**: Supplier directory, ratings, and purchase totals.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `name` (VARCHAR(255), NOT NULL)
  - `contact_email` (VARCHAR(255), NULL)
  - `total_purchases` (NUMERIC(14, 2), NOT NULL, default 0.0)
  - `rating` (NUMERIC(3, 2), NOT NULL, default 5.0)
  - `created_at` (DATETIME, NOT NULL)

#### 25. `maintenance_requests`
- **Purpose**: Scheduled and emergency machine repair tickets.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `machine_id` (UUID, FK -> machines.id, NULL)
  - `title` (VARCHAR(255), NOT NULL)
  - `status` (VARCHAR(50), NOT NULL, default "OPEN")
  - `priority` (VARCHAR(20), NOT NULL, default "MEDIUM")
  - `created_at` (DATETIME, NOT NULL)

#### 26. `notifications`
- **Purpose**: User alert routing and delivery status.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `user_id` (UUID, FK -> users.id, NOT NULL)
  - `title` (VARCHAR(255), NOT NULL)
  - `message` (TEXT, NOT NULL)
  - `notification_type` (VARCHAR(50), NOT NULL)
  - `is_read` (BOOLEAN, NOT NULL, default False)
  - `link_url` (TEXT, NULL)
  - `created_at` (DATETIME, NOT NULL)

#### 27. `integrations`
- **Purpose**: Tenant-specific third-party service connections.
- **Columns**:
  - `id` (UUID, PK, default uuid4)
  - `organization_id` (UUID, FK -> organizations.id, NOT NULL)
  - `service_name` (VARCHAR(100), NOT NULL)
  - `is_enabled` (BOOLEAN, NOT NULL, default True)
  - `config_encrypted` (TEXT, NOT NULL)
  - `created_at` (DATETIME, NOT NULL)
  - `updated_at` (DATETIME, NOT NULL)

---

# 12. Authentication

OmniAgent AI enforces stateless, cryptographic JSON Web Token (JWT) authentication using HMAC-SHA256 (`HS256`).

### Registration & Login Mechanics

1. **User Registration (`POST /api/v1/auth/register`)**:
   - Accepts `email`, `password`, `full_name`, `organization_id`, and optional `department_id`.
   - Validates that the email is unique within the organization.
   - Hashes passwords using `bcrypt` with automatically generated salts:
     ```python
     def get_password_hash(password: str) -> str:
         salt = bcrypt.gensalt()
         return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
     ```
2. **User Login (`POST /api/v1/auth/login`)**:
   - Accepts `username` (email) and `password` matching OAuth2 password specification.
   - Retrieves the user by email, verifies bcrypt password validity.
   - Emits an **Access Token** and a **Refresh Token**:
     - `ACCESS_TOKEN_EXPIRE_MINUTES`: 60 minutes.
     - `REFRESH_TOKEN_EXPIRE_DAYS`: 7 days.
     - Token payload includes `sub` (user UUID) and `type` (`access` or `refresh`).

### Token Verification Pipeline

Protected routes enforce authentication via `app.dependencies.auth.get_current_user`:
```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
) -> User:
    payload = decode_token(token)
    user_id = payload.get("sub")
    user = await UserRepository(session).get_by_id(UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials or inactive user")
    return user
```

---

# 13. Authorization and RBAC

The platform incorporates a 6-tier Role-Based Access Control (RBAC) model. Roles and permissions are persisted in the database (`roles`, `permissions`, `role_permissions`).

### System Roles Hierarchy

| System Role | Hierarchy Level | Primary Responsibilities |
| :--- | :---: | :--- |
| **Owner** | Level 6 (Highest) | Organization root account. Full administrative authority, billing, deletion. |
| **Admin** | Level 5 | System configuration, user provisioning, integration management, workflow creation. |
| **Supervisor**| Level 4 | Operational supervisor. Manages tasks and grants approvals for `HIGH` & `MEDIUM` risk actions. |
| **Operator** | Level 3 | Executes specialist agents, triggers manual workflows, initiates action requests. |
| **Auditor** | Level 2 | Read-only compliance access to audit logs, execution traces, and approval ledgers. |
| **Viewer** | Level 1 (Lowest) | Read-only access to authorized public reports, dashboards, and metrics. |

### Role-Permission Enforcement

Authorization is checked at multiple layers:
1. **Endpoint Protection**: The `require_role(allowed_roles)` dependency halts unauthorized requests before route handler execution:
   ```python
   def require_role(allowed_roles: List[str]):
       async def role_checker(current_user: User = Depends(get_current_user)) -> User:
           if not current_user.role or current_user.role.name not in allowed_roles:
               raise HTTPException(status_code=403, detail="Operation not permitted for role")
           return current_user
       return role_checker
   ```
2. **Tool Execution Guard (`ToolPermissionGuard`)**:
   - `db_read`: Admin, Supervisor, Operator
   - `email_send`: Admin, Supervisor, Operator
   - `ticket_create`: Admin, Supervisor, Operator
   - `erp_post`: Admin, Supervisor
   - `storage_delete`: Admin

---

# 14. Multi-Tenancy

OmniAgent AI implements strict logical tenant isolation across all layers:

### Data Segregation
- Every core database model incorporates an `organization_id` foreign key.
- Database access repositories (`backend/app/repositories/`) mandate `org_id` on every query, preventing cross-tenant data leakage.
- Direct database queries generated by the Database Agent are dynamically checked to ensure an explicit `WHERE organization_id = :org_id` clause is present before execution.

### Vector & Storage Isolation
- RAG embeddings in `document_chunks` store `organization_id`. Vector cosine distance queries enforce `WHERE organization_id = :org_id`.
- Document and image artifacts saved to object storage (MinIO or local filesystem) are partitioned by organizational subpaths:
  `storage/documents/{organization_id}/{document_id}/{filename}`

---

# 15. API Architecture

The backend exposes an asynchronous RESTful JSON API rooted at `/api/v1`.

### Unified Response Envelopes

All API endpoints return standardized Pydantic response models (`backend/app/schemas/common.py`):
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "metadata": {
    "request_id": "b1b7c35e-4402-4217-bfd2-646f906411ab",
    "timestamp": "2026-09-30T14:30:00Z"
  }
}
```

For paginated resources, the `PaginatedResponse[T]` envelope is returned:
```json
{
  "items": [ ... ],
  "total": 142,
  "page": 1,
  "size": 50,
  "pages": 3
}
```

### Global Error Handling

Exceptions derived from `BaseAppException` (`ValidationError`, `AuthenticationError`, `AuthorizationError`, `AgentError`, etc.) are trapped by the global exception handler in `backend/app/main.py`, returning structured JSON error payloads with diagnostic details and logging the incident to `structlog`.

---

# 16. Complete API Reference

Every endpoint across the 49 verified FastAPI routes is documented below:

### Authentication & Users

#### 1. `POST /api/v1/auth/login`
- **Method**: `POST`
- **Authentication**: None (Public)
- **Request Body**: `OAuth2PasswordRequestForm` (`username`, `password`)
- **Response**: `Token` (`access_token`, `refresh_token`, `token_type`)
- **Status Codes**: `200 OK`, `401 Unauthorized`

#### 2. `GET /api/v1/users/me`
- **Method**: `GET`
- **Authentication**: Bearer JWT
- **Response**: `ResponseEnvelope[UserRead]` (`id`, `email`, `full_name`, `role`, `organization_id`, `is_active`)
- **Status Codes**: `200 OK`, `401 Unauthorized`

### Unified Chat

#### 3. `POST /api/v1/chat`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Request Body**: `UnifiedChatRequest` (`message`, `conversation_id`, `attachments`, `context`)
- **Response**: `ResponseEnvelope[UnifiedChatResponse]` (`request_id`, `conversation_id`, `status`, `answer`, `confidence`, `grounded`, `citations`, `evidence`, `agents_used`, `execution_steps`, `action`, `approval`)
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`

#### 4. `POST /api/v1/chat/conversations/{conversation_id}/messages`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Parameters**: `conversation_id` (Path, UUID)
- **Request Body**: `MessageCreate` (`content`)
- **Response**: `ResponseEnvelope[MessageRead]` (`id`, `conversation_id`, `sender_type`, `content`, `citations`, `created_at`)
- **Status Codes**: `200 OK`, `401 Unauthorized`, `404 Not Found`

### Documents

#### 5. `GET /api/v1/documents`
- **Method**: `GET`
- **Authentication**: Bearer JWT
- **Parameters**: `skip` (Query, int, default 0), `limit` (Query, int, default 50)
- **Response**: `ResponseEnvelope[List[DocumentRead]]`
- **Status Codes**: `200 OK`, `401 Unauthorized`

#### 6. `POST /api/v1/documents/upload`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Request Body**: `multipart/form-data` with `file` (UploadFile: PDF, DOCX, TXT; max 25MB)
- **Response**: `ResponseEnvelope[DocumentRead]`
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`, `500 Internal Server Error`

#### 7. `GET /api/v1/documents/{document_id}`
- **Method**: `GET`
- **Authentication**: Bearer JWT
- **Parameters**: `document_id` (Path, UUID)
- **Response**: `ResponseEnvelope[DocumentRead]`
- **Status Codes**: `200 OK`, `401 Unauthorized`, `404 Not Found`

#### 8. `POST /api/v1/documents/{document_id}/index`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Parameters**: `document_id` (Path, UUID)
- **Response**: `ResponseEnvelope[dict]` (`document_id`, `chunks_created`, `status`)
- **Status Codes**: `200 OK`, `401 Unauthorized`, `404 Not Found`

### Vision & Images

#### 9. `POST /api/v1/agents/vision/upload`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Request Body**: `multipart/form-data` with `file` (UploadFile: JPEG, PNG, WEBP; max 10MB)
- **Response**: `ResponseEnvelope[VisionUploadResponse]` (`image_id`, `filename`, `file_size_bytes`, `storage_path`)
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`

#### 10. `GET /api/v1/agents/vision/images`
- **Method**: `GET`
- **Authentication**: Bearer JWT
- **Parameters**: `skip` (Query, int, default 0), `limit` (Query, int, default 50)
- **Response**: `ResponseEnvelope[List[dict]]`
- **Status Codes**: `200 OK`, `401 Unauthorized`

#### 11. `GET /api/v1/agents/vision/images/{image_id}`
- **Method**: `GET`
- **Authentication**: Bearer JWT
- **Parameters**: `image_id` (Path, UUID)
- **Response**: `ResponseEnvelope[dict]`
- **Status Codes**: `200 OK`, `401 Unauthorized`, `404 Not Found`

#### 12. `POST /api/v1/agents/vision/analyze`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Request Body**: `VisionAnalyzeRequest` (`image_id`, `task_type`, `prompt`, `parameters`)
- **Response**: `ResponseEnvelope[VisionAnalysisResponseData]`
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`, `404 Not Found`

### Specialist Agents Direct API

#### 13. `POST /api/v1/agents/supervisor/analyze`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Request Body**: `SupervisorAnalyzeRequest` (`message`, `context`, `attachments`)
- **Response**: `ResponseEnvelope[SupervisorAnalyzeData]` (`intent`, `task_type`, `target_agent`, `priority`, `approval_required`)
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`

#### 14. `POST /api/v1/agents/document/analyze`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Request Body**: `DocumentAnalyzeRequest` (`document_id`, `task_type`, `parameters`)
- **Response**: `ResponseEnvelope[DocumentAnalysisResponseData]`
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`

#### 15. `POST /api/v1/agents/rag/query`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Request Body**: `RAGQueryRequest` (`query`, `top_k`, `document_ids`, `filters`)
- **Response**: `ResponseEnvelope[RAGQueryResponseData]` (`answer`, `grounded`, `citations`, `retrieved_chunks`)
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`

#### 16. `POST /api/v1/agents/database/query`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Request Body**: `DatabaseQueryRequest` (`query`, `parameters`, `max_rows`)
- **Response**: `ResponseEnvelope[dict]` (`sql`, `results`, `row_count`, `summary`)
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`

#### 17. `POST /api/v1/agents/reasoning/analyze`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Request Body**: `ReasoningAnalyzeRequest` (`task`, `context`, `evidence_sources`)
- **Response**: `ResponseEnvelope[ReasoningAnalyzeResponseData]`
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`

#### 18. `POST /api/v1/agents/run`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Request Body**: `AgentRunRequest` (`agent_name`, `task_description`, `parameters`)
- **Response**: `ResponseEnvelope[AgentRunRead]`
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`

### Action Agent & Approvals

#### 19. `POST /api/v1/agents/action/execute`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Request Body**: `ActionExecuteRequest` (`action_type`, `input`, `reason`, `idempotency_key`, `approval_id`)
- **Response**: `ResponseEnvelope[ActionExecuteResponse]`
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`

#### 20. `GET /api/v1/agents/action/approvals`
- **Method**: `GET`
- **Authentication**: Bearer JWT
- **Parameters**: `status` (Query, optional, str), `skip` (Query, int), `limit` (Query, int)
- **Response**: `ResponseEnvelope[List[ActionApprovalRead]]`
- **Status Codes**: `200 OK`, `401 Unauthorized`

#### 21. `POST /api/v1/agents/action/approvals/{approval_id}/approve`
- **Method**: `POST`
- **Authentication**: Bearer JWT (Requires `Admin` or `Supervisor` role)
- **Parameters**: `approval_id` (Path, UUID)
- **Request Body**: `ActionApproveRequest` (`decision_reason`)
- **Response**: `ResponseEnvelope[ActionExecuteResponse]`
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

#### 22. `POST /api/v1/agents/action/approvals/{approval_id}/reject`
- **Method**: `POST`
- **Authentication**: Bearer JWT (Requires `Admin` or `Supervisor` role)
- **Parameters**: `approval_id` (Path, UUID)
- **Request Body**: `ActionRejectRequest` (`rejection_reason`)
- **Response**: `ResponseEnvelope[dict]`
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

#### 23. `GET /api/v1/agents/action/history`
- **Method**: `GET`
- **Authentication**: Bearer JWT
- **Parameters**: `skip` (Query, int), `limit` (Query, int)
- **Response**: `ResponseEnvelope[List[ActionHistoryItem]]`
- **Status Codes**: `200 OK`, `401 Unauthorized`

#### 24. `POST /api/v1/approvals/{approval_id}/decide`
- **Method**: `POST`
- **Authentication**: Bearer JWT (Requires `Admin` or `Supervisor` role)
- **Parameters**: `approval_id` (Path, UUID)
- **Request Body**: `ApprovalDecision` (`decision`, `reason`)
- **Response**: `ResponseEnvelope[ApprovalRead]`
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### Orchestration Workflows

#### 25. `POST /api/v1/orchestration/run`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Request Body**: `UnifiedChatRequest`
- **Response**: `ResponseEnvelope[UnifiedChatResponse]`
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`

#### 26. `GET /api/v1/orchestration/{request_id}/status`
- **Method**: `GET`
- **Authentication**: Bearer JWT
- **Parameters**: `request_id` (Path, str)
- **Response**: `ResponseEnvelope[dict]` (`request_id`, `status`, `current_agent`, `step_count`, `pending_approval`)
- **Status Codes**: `200 OK`, `401 Unauthorized`, `404 Not Found`

#### 27. `GET /api/v1/orchestration/{request_id}/events`
- **Method**: `GET`
- **Authentication**: Bearer JWT
- **Parameters**: `request_id` (Path, str)
- **Response**: `ResponseEnvelope[List[dict]]`
- **Status Codes**: `200 OK`, `401 Unauthorized`, `404 Not Found`

#### 28. `POST /api/v1/orchestration/{request_id}/resume`
- **Method**: `POST`
- **Authentication**: Bearer JWT (Requires `Admin` or `Supervisor` role)
- **Parameters**: `request_id` (Path, str)
- **Request Body**: `ResumeRequest` (`approval_id`, `decision`, `reason`)
- **Response**: `ResponseEnvelope[UnifiedChatResponse]`
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`

#### 29. `POST /api/v1/orchestration/{request_id}/cancel`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Parameters**: `request_id` (Path, str)
- **Response**: `ResponseEnvelope[dict]` (`request_id`, `status`: "CANCELLED")
- **Status Codes**: `200 OK`, `401 Unauthorized`

### Automation Workflows

#### 30. `POST /api/v1/workflows`
- **Method**: `POST`
- **Authentication**: Bearer JWT (Requires `Admin` or `Supervisor` role)
- **Request Body**: `WorkflowCreate` (`name`, `description`, `trigger_type`, `trigger_config`, `graph_definition`)
- **Response**: `ResponseEnvelope[WorkflowRead]`
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`

#### 31. `GET /api/v1/workflows`
- **Method**: `GET`
- **Authentication**: Bearer JWT
- **Parameters**: `skip` (Query, int), `limit` (Query, int)
- **Response**: `ResponseEnvelope[List[WorkflowRead]]`
- **Status Codes**: `200 OK`, `401 Unauthorized`

#### 32. `GET /api/v1/workflows/{workflow_id}`
- **Method**: `GET`
- **Authentication**: Bearer JWT
- **Parameters**: `workflow_id` (Path, UUID)
- **Response**: `ResponseEnvelope[WorkflowRead]`
- **Status Codes**: `200 OK`, `401 Unauthorized`, `404 Not Found`

#### 33. `PUT /api/v1/workflows/{workflow_id}`
- **Method**: `PUT`
- **Authentication**: Bearer JWT (Requires `Admin` or `Supervisor` role)
- **Parameters**: `workflow_id` (Path, UUID)
- **Request Body**: `WorkflowUpdate`
- **Response**: `ResponseEnvelope[WorkflowRead]`
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

#### 34. `DELETE /api/v1/workflows/{workflow_id}`
- **Method**: `DELETE`
- **Authentication**: Bearer JWT (Requires `Admin` role)
- **Parameters**: `workflow_id` (Path, UUID)
- **Response**: `ResponseEnvelope[dict]` (`deleted`: true)
- **Status Codes**: `200 OK`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

#### 35. `POST /api/v1/workflows/{workflow_id}/run`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Parameters**: `workflow_id` (Path, UUID)
- **Request Body**: `dict` (`input_payload`)
- **Response**: `ResponseEnvelope[WorkflowRunRead]`
- **Status Codes**: `200 OK`, `401 Unauthorized`, `404 Not Found`

#### 36. `GET /api/v1/workflows/{workflow_id}/runs`
- **Method**: `GET`
- **Authentication**: Bearer JWT
- **Parameters**: `workflow_id` (Path, UUID), `skip` (Query, int), `limit` (Query, int)
- **Response**: `ResponseEnvelope[List[WorkflowRunRead]]`
- **Status Codes**: `200 OK`, `401 Unauthorized`

#### 37. `GET /api/v1/workflow-runs/{run_id}`
- **Method**: `GET`
- **Authentication**: Bearer JWT
- **Parameters**: `run_id` (Path, UUID)
- **Response**: `ResponseEnvelope[WorkflowRunRead]`
- **Status Codes**: `200 OK`, `401 Unauthorized`, `404 Not Found`

#### 38. `POST /api/v1/workflow-runs/{run_id}/resume`
- **Method**: `POST`
- **Authentication**: Bearer JWT (Requires `Admin` or `Supervisor` role)
- **Parameters**: `run_id` (Path, UUID)
- **Request Body**: `dict` (`approval_decision`, `reason`)
- **Response**: `ResponseEnvelope[WorkflowRunRead]`
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`

#### 39. `POST /api/v1/workflow-runs/{run_id}/cancel`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Parameters**: `run_id` (Path, UUID)
- **Response**: `ResponseEnvelope[WorkflowRunRead]`
- **Status Codes**: `200 OK`, `401 Unauthorized`

### Integrations, Multimodal, Analytics & System

#### 40. `GET /api/v1/integrations`
- **Method**: `GET`
- **Authentication**: Bearer JWT
- **Response**: `ResponseEnvelope[List[dict]]`
- **Status Codes**: `200 OK`, `401 Unauthorized`

#### 41. `POST /api/v1/multimodal/analyze`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Request Body**: `MultimodalAnalysisRequest` (`modality`, `artifact_id`, `prompt`, `parameters`)
- **Response**: `ResponseEnvelope[MultimodalAnalysisResponse]`
- **Status Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`

#### 42. `GET /api/v1/notifications`
- **Method**: `GET`
- **Authentication**: Bearer JWT
- **Parameters**: `is_read` (Query, optional, bool), `skip` (Query, int), `limit` (Query, int)
- **Response**: `ResponseEnvelope[List[dict]]`
- **Status Codes**: `200 OK`, `401 Unauthorized`

#### 43. `GET /api/v1/analytics/overview`
- **Method**: `GET`
- **Authentication**: Bearer JWT
- **Response**: `ResponseEnvelope[dict]` (`total_conversations`, `total_agent_runs`, `total_actions`, `pending_approvals`, `token_usage`, `cost_estimate_usd`)
- **Status Codes**: `200 OK`, `401 Unauthorized`

#### 44. `GET /api/v1/health`
- **Method**: `GET`
- **Authentication**: None (Public)
- **Response**: `{"status": "healthy", "service": "omniagent-backend"}`
- **Status Codes**: `200 OK`

### API Documentation & Utility Endpoints

#### 45. `GET /api/v1/openapi.json`
- **Method**: `GET`
- **Authentication**: None
- **Response**: Complete OpenAPI 3.0 JSON specification schema.

#### 46. `GET /api/v1/docs`
- **Method**: `GET`
- **Authentication**: None
- **Response**: Interactive Swagger UI client.

#### 47. `GET /api/v1/redoc`
- **Method**: `GET`
- **Authentication**: None
- **Response**: ReDoc API documentation viewer.

#### 48. `POST /api/v1/chat/`
- **Method**: `POST`
- **Authentication**: Bearer JWT
- **Alias**: Trailing slash fallback for unified chat endpoint.

#### 49. `GET /docs/oauth2-redirect`
- **Method**: `GET`
- **Authentication**: None
- **Response**: OAuth2 redirect verification handler for Swagger UI.

---
'''
