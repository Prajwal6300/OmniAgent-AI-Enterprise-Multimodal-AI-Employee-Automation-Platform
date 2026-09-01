# OmniAgent AI — Enterprise Multimodal AI Employee & Automation Platform

[![CI/CD Pipeline](https://github.com/Prajwal6300/OmniAgent-AI-Enterprise-Multimodal-AI-Employee-Automation-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/Prajwal6300/OmniAgent-AI-Enterprise-Multimodal-AI-Employee-Automation-Platform/actions)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14.2.0-black.svg?logo=next.js)](https://nextjs.org)
[![PostgreSQL 16 + pgvector](https://img.shields.io/badge/PostgreSQL-16%20pgvector-336791.svg?logo=postgresql)](https://github.com/pgvector/pgvector)
[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph-FF6F00.svg)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

**OmniAgent AI** is a production-grade, enterprise-scale Multimodal Autonomous AI Employee and Workflow Automation Platform. It ingests and contextualizes cross-modal enterprise artifacts—ranging from scanned invoices, machine schematics, and audio voicemails to spreadsheets, relational database records, and live API feeds—to autonomously route, reason, execute, and audit complex enterprise workflows with deterministic safety and human oversight.

---

## 📑 Comprehensive Documentation Suite (`md/`)

The repository contains an exhaustive 139-document enterprise technical specification inside the [`md/`](./md/README.md) directory:

```text
md/
├── README.md                                 # Master Documentation Hub & Architecture Map
├── 01-project-overview.md                    # Platform Overview & Executive Summary
├── 02-problem-statement.md                   # Enterprise Pain Points & Solution Strategy
├── 03-goals-and-objectives.md                # Quantitative Performance SLAs & Business Targets
├── 04-features.md                            # Complete AI, Multimodal & Automation Feature Catalog
├── 05-use-cases.md                           # Cross-Departmental Real-World Enterprise Workflows
│
├── architecture/                             # System Architecture & Design
│   ├── system-architecture.md                # Multi-Layered Enterprise Topology & Flow
│   ├── component-architecture.md             # Subsystem Interfaces & Core Services
│   ├── agent-architecture.md                 # LangGraph Multi-Agent Hierarchical Supervisor Pattern
│   ├── multimodal-pipeline.md                # Asynchronous Media Ingestion & Chunking
│   ├── rag-architecture.md                   # Hybrid pgvector Dense + BM25 Sparse Search
│   ├── automation-architecture.md            # DAG Workflow Engine & Checkpointing
│   ├── data-flow.md                          # End-to-End Request, Processing & Audit Data Flow
│   └── deployment-architecture.md            # Containerized & Cloud Multi-Service Topologies
│
├── agents/                                   # Specialized Autonomous Agents
│   ├── supervisor-agent.md                   # Master Cognitive Orchestrator & Task Planner
│   ├── vision-agent.md                       # Image Anomaly Detection, OCR & Bounding Boxes
│   ├── document-agent.md                     # High-Fidelity PDF, Table & Office File Parser
│   ├── rag-agent.md                          # Enterprise Knowledge Base & Citation Engine
│   ├── database-agent.md                     # AST-Validated Parametrized Read-Only SQL Agent
│   ├── reasoning-agent.md                    # 3-Way Match Reconciler & Risk Scorer
│   └── action-agent.md                       # External Tool Actuator (ERP, Slack, Jira, Email)
│
├── ai/                                       # AI Subsystems & Guardrails
│   ├── llm-architecture.md                   # Multi-Model Dynamic Gateway & Circuit Breakers
│   ├── multimodal-ai.md                      # Unified Cross-Modal Feature Alignment
│   ├── prompt-architecture.md                # Role Prompts, Dynamic Delimiters & Delimiter Framing
│   ├── rag-pipeline.md                       # Semantic Token Chunking, Embeddings & Reranking
│   ├── embeddings.md                         # BAAI/bge-large-en-v1.5 & Vector Math
│   ├── memory.md                             # Working State, Session Buffers & Long-Term Recall
│   ├── tool-calling.md                       # Deterministic Pydantic Tool Schemas & Auto-Healing
│   ├── hallucination-control.md              # Two-Pass Fact Grounding & Explicit Refusal
│   └── prompt-injection-protection.md       # Untrusted Content Sandboxing & Firewalls
│
├── automation/                               # Workflow Automation & Governance
│   ├── workflow-engine.md                    # Distributed State Machine & Fault Tolerance
│   ├── triggers.md                           # Webhook, S3 Upload, Cron, Email & Manual Triggers
│   ├── conditions.md                         # AST Sandboxed Boolean Expression Rule Engine
│   ├── actions.md                            # Centralized Action & Tool Registry
│   ├── human-in-the-loop.md                  # 3-Tier Risk Engine (LOW, MEDIUM, HIGH)
│   ├── approval-system.md                    # Next.js Approval Inbox & HMAC Digital Signatures
│   └── example-workflows.md                  # Verified JSON/YAML Production Workflow DAGs
│
├── multimodal/                               # Media Extraction & Normalization
│   ├── text-processing.md                    # Plaintext, Markdown & HTML Sanitization
│   ├── pdf-processing.md                     # PyMuPDF + pdfplumber Layout & Table Extraction
│   ├── document-processing.md                # DOCX, PPTX, XLSX & CSV Ingestion
│   ├── image-processing.md                   # OpenCV CLAHE, Deskewing & Visual Anomaly Filters
│   ├── ocr.md                                # Hybrid Tesseract & Vision LLM OCR
│   ├── audio-processing.md                   # Faster-Whisper ASR Speech-to-Text Pipeline
│   ├── video-processing.md                   # Keyframe Extraction & Temporal Alignment
│   └── structured-data-processing.md         # Dataframe Linearization & DuckDB SQL Ingestion
│
├── backend/                                  # Backend Service Core
│   ├── backend-architecture.md               # FastAPI Async Lifespan & Directory Layout
│   ├── api-architecture.md                   # RESTful Conventions, SSE Streams & WebSockets
│   ├── authentication.md                     # OAuth2 Password Flow & JWT Refresh Rotation
│   ├── authorization-rbac.md                 # 6-Tier Enterprise Role-Based Access Control
│   ├── database.md                           # SQLAlchemy 2.0 Asyncpg Connection Pools
│   ├── background-jobs.md                    # Celery Distributed Workers & Redis Queues
│   ├── caching.md                            # Redis Key Namespaces & Rate Limiting
│   ├── file-storage.md                       # S3 / MinIO Presigned URL Security
│   └── error-handling.md                     # Global RFC 7807 Problem Detail Handlers
│
├── frontend/                                 # Web Application
│   ├── frontend-architecture.md              # Next.js 14 App Router, TypeScript & Shadcn UI
│   ├── pages.md                              # Application Views, Layouts & Route Hierarchy
│   ├── components.md                         # Reusable UI Primitives & Domain Components
│   ├── state-management.md                   # Zustand Client Stores & React Query Cache
│   ├── api-integration.md                    # Axios Interceptors & SSE Event Consumers
│   └── ui-ux-guidelines.md                   # Design Tokens, High-Contrast Risk Badges & WCAG AA
│
├── security/                                 # Enterprise Security & Compliance
│   ├── security-overview.md                  # 7-Layer Defense-in-Depth Model
│   ├── authentication-security.md            # Token Signing, Expiration & Password Policies
│   ├── authorization-security.md            # Multi-Tenant Row-Level Security (RLS)
│   ├── file-security.md                      # Magic Byte Validation & Sandboxed Extraction
│   ├── prompt-security.md                    # Delimiter Framing & Jailbreak Prevention
│   ├── api-security.md                       # Token Bucket Rate Limiting & Security Headers
│   ├── data-privacy.md                       # PII Masking, Data Redaction & GDPR / HIPAA
│   └── audit-logging.md                      # HMAC SHA-256 Tamper-Proof Audit Ledger
│
├── database/                                 # Database Architecture & Schemas
│   ├── database-overview.md                  # PostgreSQL 16 + pgvector Strategy
│   ├── schema.md                             # Complete DDL Table & Extension Definitions
│   ├── relationships.md                      # Mermaid ER Diagrams & Foreign Key Rules
│   ├── indexes.md                            # HNSW Vector, GIN Full-Text & B-Tree Indexes
│   ├── migrations.md                         # Alembic Version History & Migration Commands
│   └── data-retention.md                     # Partitioning Strategy & Data Lifecycle Policies
│
├── api/                                      # API Reference & Endpoints
│   ├── api-overview.md                       # Base URLs, Headers & Envelope Formats
│   ├── authentication-api.md                 # /api/v1/auth (Login, Refresh, Me)
│   ├── chat-api.md                           # /api/v1/chat (Sessions & SSE Stream)
│   ├── document-api.md                       # /api/v1/documents (Presigned Uploads & Ingestion)
│   ├── multimodal-api.md                     # /api/v1/multimodal (Vision & Audio Inspect)
│   ├── agent-api.md                          # /api/v1/agents (Execution & Traces)
│   ├── workflow-api.md                       # /api/v1/workflows (DAG CRUD & Trigger)
│   ├── approval-api.md                       # /api/v1/approvals (Pending & Decide)
│   └── health-api.md                         # /api/v1/health (Liveness & Readiness Probes)
│
├── integrations/                             # Enterprise System Connectors
│   ├── integration-overview.md               # Connector Abstraction Layer & Vault Storage
│   ├── email.md                              # SMTP & SendGrid Notification Services
│   ├── slack.md                              # Slack Block Kit Webhooks & ChatOps
│   ├── erp.md                                # SAP S/4HANA & Oracle REST API Connectors
│   ├── web-search.md                         # Tavily & DuckDuckGo Search Engines
│   └── external-apis.md                      # Generic Declarative Tool Framework
│
├── workflows/                                # Production Enterprise Workflows
│   ├── invoice-automation.md                 # 3-Way Match AP Reconciliation & Posting
│   ├── hr-automation.md                      # Employee Leave & Policy Q&A Synthesizer
│   ├── it-support-automation.md              # Screenshot Error Diagnosis & Jira Incidents
│   ├── manufacturing-automation.md           # Defect Visual Inspection & SAP Work Orders
│   ├── customer-support-automation.md        # Multimodal Ticket Triage & RMA Processing
│   └── report-automation.md                  # Dataframe Aggregations & PDF Briefings
│
├── development/                              # Developer Experience
│   ├── development-setup.md                  # Toolchain & Step-by-Step Setup Guide
│   ├── environment-variables.md              # Complete .env Variable Matrix & Defaults
│   ├── local-development.md                  # Multi-Terminal Startup & Database Seeding
│   ├── coding-standards.md                   # Black, Ruff, Mypy Strict & ESLint Standards
│   ├── git-workflow.md                       # GitHub Flow & Conventional Commits
│   └── troubleshooting.md                    # Top 10 Development & Runtime Solutions
│
├── testing/                                  # Quality Assurance & Verification
│   ├── testing-strategy.md                   # Enterprise Testing Pyramid & Execution Commands
│   ├── unit-testing.md                       # Pytest & Vitest Unit Test Suites
│   ├── integration-testing.md                # PostgreSQL 16 Testcontainers Suite
│   ├── api-testing.md                        # Automated E2E API Regression & Postman
│   ├── agent-testing.md                      # Deterministic Multi-Agent Trajectory Assertions
│   ├── rag-evaluation.md                     # Ragas Groundedness & Relevance Benchmarks
│   └── security-testing.md                   # Bandit SAST & Adversarial Prompt Red-Teaming
│
├── deployment/                               # Deployment & Infrastructure
│   ├── deployment-overview.md                # On-Premise, Hybrid & Cloud Matrices
│   ├── docker.md                             # Multi-Stage Dockerfile & Docker Compose Stack
│   ├── production.md                         # Gunicorn/Uvicorn Tuning & Nginx TLS Reverse Proxy
│   ├── environment-configuration.md          # Dev, Staging & Production Profiles
│   ├── cloud-deployment.md                   # AWS Enterprise VPC & ECS Architecture Spec
│   ├── ci-cd.md                              # GitHub Actions CI/CD Pipeline
│   └── monitoring.md                         # Prometheus Metrics & PagerDuty Alert Rules
│
├── observability/                            # Telemetry & Monitoring
│   ├── logging.md                            # structlog JSON Structured Logs & Context
│   ├── metrics.md                            # Prometheus Metrics & Endpoint Latencies
│   ├── tracing.md                            # OpenTelemetry Distributed Spans
│   ├── agent-traces.md                       # Multi-Agent Latency Waterfall Timelines
│   ├── performance.md                        # Benchmarks (TTFT, Vector Search, Concurrency)
│   └── cost-monitoring.md                    # Token Counter & Departmental USD Cost Attribution
│
├── product/                                  # Product Specifications
│   ├── user-roles.md                         # Persona Definitions & Permissions Matrix
│   ├── user-journeys.md                      # Step-by-Step Interactive User Workflows
│   ├── dashboard.md                          # Executive & Operational Metrics Dashboard
│   ├── notifications.md                      # Notification Center & Urgency Routing
│   └── settings.md                           # Organization Profile, Models & Integrations
│
├── decisions/                                # Architecture Decision Records (ADR)
│   ├── architecture-decisions.md             # ADR 001: LangGraph Multi-Agent Orchestration
│   ├── technology-decisions.md               # ADR 002: FastAPI, PostgreSQL 16 + pgvector, Next.js
│   └── ai-model-decisions.md                 # ADR 003: Dynamic Multi-Tier Model Gateway
│
├── roadmap/                                  # Project Lifecycle & Status
│   ├── roadmap.md                            # Phases 1 through 9 Evolution Plan
│   ├── current-status.md                     # Complete System Implementation Audit Matrix
│   ├── future-features.md                    # Next-Generation Autonomous AI Horizon
│   └── known-limitations.md                  # Known Operational Constraints & Mitigations
│
└── portfolio/                                # Career & Presentation Assets
    ├── resume-description.md                 # High-Impact Resume Summaries & Technical Bullets
    ├── linkedin-description.md               # Professional Project Announcement Post
    ├── portfolio-description.md              # Detailed Web Portfolio Case Study
    ├── github-description.md                 # Open-Source README Showcase & Topics
    ├── interview-explanation.md              # 20-Question In-Depth Technical Interview Guide
    └── demo-script.md                        # 5-Minute High-Impact Live Demonstration Script
```

---

## 🏛️ System Architecture Flow

```text
User / Business Event
        ↓
Multimodal Input (Text, PDF, DOCX, XLSX, Images, Audio, Video)
        ↓
AI Supervisor Agent (LangGraph Controller)
        ↓
Specialized Agents (Vision, Document, RAG, Database, Reasoning)
        ↓
Enterprise Knowledge Grounding (PostgreSQL 16 + pgvector, ERP Data)
        ↓
Deterministic Policy & Tool Calling
        ↓
Human-in-the-Loop Approval Gate (LOW / MEDIUM / HIGH Risk)
        ↓
Real-World Action & External Sync (SAP, Slack, Jira, SMTP)
        ↓
Verification & Immutable Audit Ledger (HMAC SHA-256)
```

---

## 🚀 Key Technology Stack

* **Backend Engine:** FastAPI (Python 3.11+), Uvicorn ASGI, Pydantic v2
* **Agent Orchestrator:** LangGraph, LangChain Core
* **Database & Vector Store:** PostgreSQL 16 with `pgvector` (HNSW indexing) & SQLAlchemy 2.0 Async
* **Task Queues & In-Memory Cache:** Redis 7+ with Celery Workers
* **Object Storage:** MinIO / AWS S3 Compatible API
* **Frontend Portal:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Shadcn UI
* **Multimodal Libraries:** PyMuPDF, pdfplumber, OpenCV, Tesseract OCR, Faster-Whisper, Pandas
* **Foundation LLMs:** Anthropic Claude 3.5 Sonnet, OpenAI GPT-4o, Google Gemini 1.5 Pro, Local Ollama (Llama 3.3 70B)

---

## ⚡ Quick Start

```bash
# 1. Clone repository
git clone https://github.com/Prajwal6300/OmniAgent-AI-Enterprise-Multimodal-AI-Employee-Automation-Platform.git
cd OmniAgent-AI-Enterprise-Multimodal-AI-Employee-Automation-Platform

# 2. Start infrastructure containers
docker compose up -d postgres redis minio

# 3. Start Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 4. Start Frontend
cd ../frontend
npm install && npm run dev
```

---

## 📄 License
This project is licensed under the Apache 2.0 License.
