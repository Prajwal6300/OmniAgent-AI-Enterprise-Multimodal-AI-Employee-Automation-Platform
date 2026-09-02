# OmniAgent AI

Enterprise Multimodal AI Employee & Automation Platform

[![CI Pipeline](https://github.com/Prajwal6300/OmniAgent-AI-Enterprise-Multimodal-AI-Employee-Automation-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/Prajwal6300/OmniAgent-AI-Enterprise-Multimodal-AI-Employee-Automation-Platform/actions)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3.1-61DAFB.svg?logo=react)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6.svg?logo=typescript)](https://www.typescriptlang.org)
[![PostgreSQL 16 + pgvector](https://img.shields.io/badge/PostgreSQL-16%20pgvector-336791.svg?logo=postgresql)](https://github.com/pgvector/pgvector)
[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph-FF6F00.svg)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

---

## Overview

**OmniAgent AI** is a production-grade enterprise multimodal AI employee and autonomous workflow platform. Built to solve modern enterprise productivity bottlenecks, OmniAgent AI ingests, normalizes, reasons over, and acts upon cross-modal enterprise data—including scanned PDFs, office documents, system screenshots, audio dictation, operational video streams, spreadsheets, and live SQL databases.

Unlike conversational chatbots that produce passive text responses, OmniAgent AI executes real-world business workflows. It coordinates specialized autonomous AI agents, connects to enterprise systems via controlled tools, calculates risk levels for every potential operation, enforces human-in-the-loop approvals for sensitive actions, and maintains an immutable, tamper-proof audit trail for regulatory compliance.

---

## Why OmniAgent AI?

Modern enterprise knowledge and operations are fragmented across unstructured formats (PDFs, emails, voicemail recordings, diagrams) and structured silos (relational databases, ERPs, ticketing tools). Existing point solutions suffer from:

1. **Modal Silos**: OCR tools extract text without contextual reasoning, while conversational LLMs lack direct multi-page layout and image parsing capabilities.
2. **Uncontrolled Tool Execution**: Fragile ReAct agents with unrestricted SQL or API access risk data corruption, unauthorized disclosures, and non-compliance.
3. **Lack of Human Oversight**: Enterprises cannot deploy autonomous agents without strict approval gates, deterministic role-based boundaries, and step-by-step verifiable traces.
4. **Poor Auditability**: Black-box agent architectures fail enterprise SOC 2, HIPAA, and GDPR compliance standards.

OmniAgent AI solves these challenges with a modular, multi-tenant architecture uniting hierarchical agent coordination, deterministic tool sandboxing, hybrid pgvector RAG, and an automated approval engine.

---

## Key Features

- **Cross-Modal Data Ingestion**: Seamless ingestion and parsing of Text, PDF (tables and layout), DOCX, PPTX, Images (OCR and anomaly detection), Audio (Whisper ASR), Video (keyframes), and Structured Data (CSV/Excel).
- **Hierarchical Multi-Agent Graph**: Dynamic task decomposition via a master Supervisor Agent orchestrating Vision, Document, RAG, Database, Reasoning, and Action agents.
- **Enterprise Hybrid RAG**: High-accuracy semantic vector search powered by PostgreSQL `pgvector` paired with BM25 keyword matching, metadata filtering, and reciprocal rank fusion.
- **Controlled Actuation & Tools**: Pre-built enterprise connectors for PostgreSQL, ERP systems (SAP/Oracle), Email (SMTP/SendGrid), Ticket management (Jira/ServiceNow), and Web search with strict permission gating.
- **Human-in-the-Loop Risk Gating**: 3-tiered risk model (LOW, MEDIUM, HIGH) that automatically pauses dangerous tasks until designated managers grant cryptographically signed approvals.
- **Full Traceability & Audit Ledger**: HMAC SHA-256 tamper-proof logging of every agent reasoning token, tool call, input parameter, response, and human intervention.
- **Multi-Tenant RBAC & Security**: Native tenant isolation (`organization_id`), 6-tiered role hierarchy, JWT auth with refresh rotation, and prompt injection defense.

---

## Architecture

OmniAgent AI is architected as a modular, enterprise-ready monolith with clean layer isolation and clear boundaries for horizontal microservice extraction:

```text
User / Event Trigger
         │
         ▼
┌────────────────────────────────────────────────────────┐
│               Frontend Web Application                 │
│         (React 18, TypeScript, Vite, Tailwind)         │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTPS / SSE / WebSockets
                           ▼
┌────────────────────────────────────────────────────────┐
│                  FastAPI Backend Gateway               │
│   (Auth, RBAC, Request Validation, Rate Limiter)       │
└────────┬─────────────────┬───────────────────┬─────────┘
         │                 │                   │
         ▼                 ▼                   ▼
┌─────────────────┐ ┌─────────────┐ ┌────────────────────┐
│ Multi-Agent     │ │ Multimodal  │ │ Workflow &         │
│ Orchestrator    │ │ Processing  │ │ Automation Engine  │
│ (LangGraph)     │ │ Pipeline    │ │ (DAG State Machine)│
└────────┬────────┘ └──────┬──────┘ └──────────┬─────────┘
         │                 │                   │
         ▼                 ▼                   ▼
┌────────────────────────────────────────────────────────┐
│             Controlled Enterprise Tools Layer          │
│   (DB Queries, ERP Sync, Tickets, Email, Storage)      │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│            Human-in-the-Loop Approval Gate             │
│   [Risk Evaluation: LOW (Auto) | HIGH (Require Sign)]  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│             Persistence & Infrastructure               │
│ (PostgreSQL 16 + pgvector, Redis 7, Celery, MinIO/S3) │
└────────────────────────────────────────────────────────┘
```

---

## AI Agents

The agent layer is decoupled from API and database connections, orchestrating tasks via a directed state graph:

1. **Supervisor Agent**: Decomposes user goals, routes intermediate steps to specialists, evaluates task convergence, and synthesizes final responses.
2. **Vision Agent**: Inspects images, blueprints, and diagrams, detecting visual anomalies, bounding boxes, and extracting text from complex scenes.
3. **Document Agent**: Extracts high-fidelity hierarchies, form fields, and nested tables from multi-page PDFs, Word documents, and presentations.
4. **RAG Agent**: Queries pgvector collections, reranks context candidates, and grounds answers with exact document citations.
5. **Database Agent**: Translates questions into AST-validated, read-only parametrized SQL queries against approved schema mirrors.
6. **Reasoning Agent**: Performs mathematical checks, 3-way reconciliation (e.g., PO vs. Invoice vs. Delivery note), and risk assessments.
7. **Action Agent**: Formulates and executes tool actions against ERPs, notifications, ticket systems, and storage backends.

---

## Multimodal Capabilities

OmniAgent AI supports comprehensive media normalization pipelines under `multimodal/`:

- **Text**: Plaintext, Markdown, HTML cleaning, language detection, and token normalization.
- **PDF**: PyMuPDF and pdfplumber extraction for layout preservation, vector bounding boxes, and table reconstruction.
- **Office Documents**: DOCX, PPTX slide-by-slide paragraph and metadata extraction.
- **Images**: OpenCV preprocessing (CLAHE, deskewing), object classification, and vision LLM inspections.
- **OCR**: Dual-mode Tesseract and multimodal vision model OCR with confidence scoring.
- **Audio**: Faster-Whisper ASR speech-to-text with speaker diarization and timestamp alignment.
- **Video**: Keyframe extraction, scene boundary detection, and multimodal frame analysis.
- **Structured Data**: CSV/Excel automated schema inference, missing value imputation, and DuckDB analytical query execution.

---

## RAG

The RAG subsystem (`backend/app/services/rag/`) delivers enterprise semantic retrieval:

- **Chunking**: Recursive character and semantic token chunking preserving section boundaries.
- **Dense Embeddings**: Pluggable support for OpenAI `text-embedding-3-large`, BAAI BGE models, or local HuggingFace embeddings.
- **Hybrid Retrieval**: PostgreSQL 16 `pgvector` HNSW cosine distance search combined with full-text GIN index BM25 ranking.
- **Reranking**: Cross-encoder rerankers prioritize the top-k most contextually relevant passages.
- **Grounding & Citations**: Explicit bracketed citations with page numbers and document hashes to guarantee zero hallucinations.
- **Tenant Isolation**: Mandatory `organization_id` filter appended to all vector similarity queries at the database engine level.

---

## Automation

The automation engine (`automation/`) powers headless, event-driven DAG workflows:

- **Triggers**: Webhook events, file uploads, scheduled cron jobs, inbound emails, and database change feeds.
- **Conditions**: Sandboxed AST boolean expression evaluator for business rules.
- **Action Nodes**: API dispatches, database record creation, email alerts, PDF report generation, and external ticket creation.
- **Approval Engine**: Risk-scored checkpoints where state machines transition to `AWAITING_APPROVAL`, notifying authorized reviewers.
- **Production Templates**: Ready-to-use workflows for AP Invoice Processing, HR Onboarding, IT Incident Triage, and Manufacturing Quality Inspections.

---

## Enterprise Security

- **Multi-Tenant Isolation**: Row-Level Security (RLS) guarantees data segregation across tenants.
- **RBAC Matrix**: 6 granular roles (`Owner`, `Admin`, `Supervisor`, `Operator`, `Auditor`, `Viewer`).
- **Cryptographic Audit Log**: Immutable SHA-256 hash chains capturing all events, tool calls, and user decisions.
- **Prompt Injection Defense**: Multi-stage delimiter framing, system prompt anchoring, and untrusted payload sandboxing.
- **SQL Safety**: Parameterized queries, read-only connection pools, AST validation, and prohibited destructive DDL/DML keywords.
- **File Validation**: Strict magic byte validation and anti-virus / malformed zip bomb inspection.

---

## Tech Stack

| Layer | Technologies |
| --- | --- |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query, React Router |
| **Backend API** | Python 3.11+, FastAPI, Pydantic v2, Uvicorn, Celery |
| **Orchestration** | LangGraph, LangChain Core |
| **Database & Vector** | PostgreSQL 16, pgvector (HNSW), SQLAlchemy 2.0 (Asyncpg), Alembic |
| **Cache & Message Broker** | Redis 7, Celery Distributed Workers |
| **Object Storage** | MinIO / AWS S3 |
| **Multimodal Processing**| PyMuPDF, pdfplumber, OpenCV, Tesseract, Faster-Whisper, Pandas, DuckDB |
| **DevOps & Monitoring** | Docker, Docker Compose, Nginx, Prometheus, Grafana, GitHub Actions |

---

## Project Structure

```text
OmniAgent-AI/
├── README.md                      # Platform overview and reference
├── LICENSE                        # Apache 2.0 open-source license
├── .gitignore                     # Production Git ignore configuration
├── .env.example                   # Master environment variable template
├── docker-compose.yml             # Multi-service local & production stack
├── Makefile                       # Developer automation commands
├── CONTRIBUTING.md                # Contribution guidelines
├── SECURITY.md                    # Enterprise security and disclosure policies
│
├── frontend/                      # React 18 + TypeScript + Vite SPA
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── src/
│       ├── components/            # shadcn/ui and domain-specific components
│       ├── pages/                 # Route views (Dashboard, Chat, Approvals, etc.)
│       ├── services/              # API and WebSocket service clients
│       ├── store/                 # Global state management
│       └── types/                 # TypeScript interfaces and contracts
│
├── backend/                       # FastAPI Core Backend Service
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── alembic.ini
│   └── app/
│       ├── api/                   # Versioned REST endpoints (/api/v1)
│       ├── core/                  # Config, security, logging, exceptions
│       ├── db/                    # SQLAlchemy async session and engine
│       ├── models/                # Database entities (User, Workflow, AuditLog, etc.)
│       ├── schemas/               # Pydantic validation schemas
│       ├── repositories/          # Clean database access abstractions
│       ├── services/              # Business logic services & RAG pipeline
│       ├── workers/               # Asynchronous Celery background workers
│       └── utils/                 # Helpers, pagination, and file validators
│
├── agents/                        # Multi-Agent Coordination Layer (LangGraph)
│   ├── graph/                     # State graph, node definitions, conditional routing
│   ├── supervisor/                # Master orchestration agent
│   ├── vision/                    # Image and visual inspection agent
│   ├── document/                  # Deep document extraction agent
│   ├── rag/                       # Semantic retrieval agent
│   ├── database/                  # Controlled SQL generation agent
│   ├── reasoning/                 # Business logic and reconciliation agent
│   ├── action/                    # External tool execution agent
│   ├── memory/                    # Short-term, long-term, and working memory
│   ├── prompts/                   # Formatted prompt templates
│   └── evaluation/                # Trajectory testing and benchmarks
│
├── multimodal/                    # Specialized Media Parsers & Normalizers
│   ├── text/                      # Text sanitization and normalizers
│   ├── pdf/                       # PDF parser, layout analyzer, table extractor
│   ├── documents/                 # DOCX, PPTX, and Office file parsers
│   ├── image/                     # OpenCV image filters and vision processing
│   ├── ocr/                       # Tesseract and vision-based OCR engines
│   ├── audio/                     # Faster-Whisper ASR transcription
│   ├── video/                     # Video keyframe extraction and analysis
│   └── structured_data/           # CSV and Excel schema inference and DuckDB queries
│
├── tools/                         # Secure Agent Tool Actuators
│   ├── database/                  # Validated SQL query executors
│   ├── email/                     # SMTP and SendGrid messaging
│   ├── notifications/             # Webhook and push notification dispatchers
│   ├── reports/                   # Automated PDF and Excel report generation
│   ├── tickets/                   # Jira and ServiceNow issue managers
│   ├── web/                       # Search engine and web page fetchers
│   ├── storage/                   # Presigned upload/download storage operations
│   ├── erp/                       # SAP and Oracle ERP adapter clients
│   └── common/                    # Tool registry and permission checkers
│
├── automation/                    # Headless Workflow Automation Engine
│   ├── engine/                    # DAG workflow state machine and scheduler
│   ├── triggers/                  # Webhook, schedule, upload, and manual triggers
│   ├── conditions/                # AST-sandboxed condition evaluators
│   ├── actions/                   # Workflow action executors
│   ├── approvals/                 # Risk evaluator and approval manager
│   └── workflows/                 # Standard enterprise workflow definitions
│
├── database/                      # Persistence Specifications & Migrations
│   ├── schema/                    # Raw DDL schema.sql and ERD documentation
│   ├── seeds/                     # Seed data for initial configuration
│   └── migrations/                # Version migration instructions
│
├── infrastructure/                # Containerization, Reverse Proxy & Cloud
│   ├── docker/                    # Dockerfiles for Frontend, Backend, and Worker
│   ├── nginx/                     # Reverse proxy and SSL configuration
│   ├── postgres/                  # Postgres pgvector initialization
│   ├── redis/                     # Redis cache configuration
│   ├── cloud/                     # AWS ECS and Vercel configs
│   ├── monitoring/                # Prometheus and Grafana dashboards
│   └── scripts/                   # Deployment and backup automation
│
├── tests/                         # Automated Enterprise Test Suite
│   ├── unit/                      # Unit tests for backend, agents, rag, multimodal
│   ├── integration/               # Database, API, and workflow integration tests
│   ├── e2e/                       # End-to-end user scenario tests
│   ├── security/                  # Auth, RBAC, SQL safety, and injection tests
│   ├── evaluation/                # Ragas groundedness and agent accuracy benchmarks
│   └── fixtures/                  # Reusable mock datasets and sample files
│
├── scripts/                       # Developer Tooling & Automation
│   ├── setup.sh / setup.ps1       # Environment setup scripts
│   ├── dev.sh / dev.ps1           # Development start scripts
│   ├── test.sh / lint.sh          # Testing and code verification scripts
│   ├── migrate.sh                 # Database migration execution
│   └── seed.py / healthcheck.py   # Seeding and system diagnostic utilities
│
├── docs/                          # Engineering Documentation
│   ├── architecture/              # High-level design documents
│   ├── api/                       # API reference manuals
│   ├── development/               # Developer setup guides
│   ├── deployment/                # Production infrastructure guides
│   └── security/                  # Security whitepapers
│
└── md/                            # Comprehensive 139-Document Specification Suite
```

---

## Installation

### Prerequisites
- Docker & Docker Compose (v2.20+)
- Python 3.11+
- Node.js 20+ & npm

### Clone Repository
```bash
git clone https://github.com/Prajwal6300/OmniAgent-AI-Enterprise-Multimodal-AI-Employee-Automation-Platform.git
cd OmniAgent-AI-Enterprise-Multimodal-AI-Employee-Automation-Platform
```

### Initial Setup
Run the unified setup script for your platform:

**Linux / macOS:**
```bash
chmod +x scripts/*.sh
./scripts/setup.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\setup.ps1
```

---

## Environment Variables

Copy the example environment configurations:
```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Configure your LLM provider credentials and database connections:
- `DATABASE_URL`: Async PostgreSQL connection string with pgvector support
- `REDIS_URL`: Redis broker and caching URI
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`: API keys for foundation models
- `JWT_SECRET`: High-entropy key for token generation
- `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`: Storage service credentials

---

## Running Locally

### Option A: Using Docker Compose (Full Stack)
```bash
docker compose up -d
```
The services will be accessible at:
- Frontend UI: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/docs`
- MinIO Console: `http://localhost:9001`

### Option B: Local Development (Hot Reloading)

1. **Start Core Infrastructure:**
   ```bash
   docker compose up -d postgres redis minio
   ```

2. **Start Backend API:**
   ```bash
   cd backend
   source venv/bin/activate  # Or: venv\Scripts\activate on Windows
   alembic upgrade head
   uvicorn app.main:app --reload --port 8000
   ```

3. **Start Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```
   Access the frontend at `http://localhost:5173`.

---

## Testing

Run the comprehensive test suite:

```bash
# Run all unit and integration tests
pytest tests/ -v

# Run security and prompt injection tests
pytest tests/security/ -v

# Run agent evaluation benchmarks
pytest tests/evaluation/ -v
```

---

## Deployment

OmniAgent AI is designed for containerized deployment across major cloud providers:

- **AWS ECS / Fargate**: Pre-configured task definition available in `infrastructure/cloud/aws/ecs-task-definition.json`.
- **Nginx Reverse Proxy**: Production SSL and reverse proxy configuration under `infrastructure/nginx/nginx.conf`.
- **Frontend CDN**: Static bundle deployment configuration for Vercel/Cloudflare in `infrastructure/cloud/vercel/vercel.json`.

---

## Example Workflows

1. **Autonomous AP Invoice Processing**:
   - Inbound invoice PDF arrives via webhook/email.
   - Document Agent extracts vendor, line items, and tax data.
   - Database Agent queries ERP purchase orders.
   - Reasoning Agent performs a 3-way match.
   - If mismatch is > 5%, an approval request is routed to the department manager.
   - Upon cryptographic approval, Action Agent posts payment via SAP adapter.

2. **IT Incident Diagnostic & Resolution**:
   - User submits screenshot of application error message.
   - Vision Agent extracts error code and stack trace.
   - RAG Agent checks runbook documentation in pgvector knowledge base.
   - Supervisor Agent recommends remediation steps and drafts a Jira ticket.

---

## Screenshots

*(UI mockups and interactive screenshots will be populated upon initial deployment)*

- **Executive Dashboard**: Real-time throughput, active agent runs, pending approvals, and cost per department.
- **Multimodal Chat Console**: Unified conversation view displaying live agent reasoning traces, document citations, and image bounding boxes.
- **Human Approval Inbox**: Granular risk evaluation display with one-click cryptographic decisioning.

---

## Demo

To run a simulated agent workflow demonstration:
```bash
python scripts/healthcheck.py
```
This utility validates database connectivity, pgvector extensions, Redis cache responsiveness, and LLM gateway availability.

---

## Roadmap

- [x] Foundation multi-tenant database schema & pgvector HNSW indexing
- [x] Hierarchical LangGraph Supervisor architecture
- [x] Multimodal parsing pipelines (PDF, Images, Audio, Video, CSV)
- [x] Controlled tools layer with RBAC and risk evaluation
- [x] Human-in-the-loop approval state machine
- [ ] Enterprise SSO (SAML 2.0 / Okta / Azure AD)
- [ ] Multi-region active-active pgvector replication
- [ ] On-premise air-gapped LLM inference support (vLLM / Ollama)

---

## License

This project is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for details.
