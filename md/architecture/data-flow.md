# Architecture — Data Flow & Request Lifecycle

## Status
**Status:** ✅ IMPLEMENTED (End-to-End Synchronous & Asynchronous Pipelines)

---

## 1. End-to-End Request Lifecycle

The diagram below traces the end-to-end data flow when an enterprise user or automated trigger sends a multimodal task to OmniAgent AI.

```mermaid
sequenceDiagram
    autonumber
    actor User as Enterprise Operator
    participant UI as Next.js Web Portal
    participant API as FastAPI Gateway
    participant S3 as MinIO / S3 Storage
    participant Graph as LangGraph Supervisor
    participant Agent as Specialized Agent Swarm
    participant DB as PostgreSQL 16 + pgvector
    participant Ext as External System (ERP / Slack)
    participant Audit as Immutable Audit Ledger

    User->>UI: Uploads Invoice PDF + Submits Request
    UI->>S3: Stream raw binary via Presigned URL
    S3-->>UI: Upload Acknowledged (S3 Key)
    UI->>API: POST /api/v1/chat (Prompt + S3 Key)
    API->>API: Validate JWT, Tenant ID & RBAC
    API->>Graph: Initialize LangGraph State Machine
    
    Graph->>Agent: Route to Document Agent (Extract PDF)
    Agent->>S3: Fetch binary & execute PyMuPDF/OCR
    Agent-->>Graph: Structured JSON Line Items
    
    Graph->>Agent: Route to Database Agent (Fetch PO/GR)
    Agent->>DB: Query Relational Tables (Read-Only AST SQL)
    DB-->>Agent: Purchase Order & Goods Receipt Records
    Agent-->>Graph: PO Data
    
    Graph->>Agent: Route to Reasoning Agent (Validate Policy)
    Agent-->>Graph: 3-Way Match Verified; High Risk Action Proposed
    
    Graph->>API: Suspend Execution (Pending Human Approval)
    API-->>UI: Push Approval Modal (SSE / WebSocket)
    
    User->>UI: Clicks "Approve & Post to ERP"
    UI->>API: POST /api/v1/approvals/{id}/decide (Approved)
    API->>Graph: Resume Graph Execution
    
    Graph->>Agent: Route to Action Agent (Execute ERP Mutation)
    Agent->>Ext: POST /api/v1/erp/invoices (Idempotency-Key)
    Ext-->>Agent: HTTP 201 Created (ERP Invoice #99812)
    Agent-->>Graph: Mutation Complete
    
    Graph->>Audit: Append Signed HMAC Audit Entry
    Audit->>DB: Write Immutable Audit Row
    Graph-->>API: Graph Traversal Complete
    API-->>UI: Stream Final Response & Verification Summary
    UI-->>User: Render Interactive Completion Card
```

---

## 2. In-Flight Data Transformation Stages

| Stage | Input Representation | Transformation Engine | Output Representation |
| :--- | :--- | :--- | :--- |
| **1. Ingestion** | Raw Multipart Binary Stream | S3 Client + Magic Byte Validator | Encrypted S3 URI + SHA-256 Hash |
| **2. Extraction** | S3 Binary Stream | PyMuPDF / Tesseract / Whisper | Clean Markdown + Structured JSON |
| **3. Vectorization** | Normalized Text Chunks | BAAI/bge-large-en-v1.5 Model | 1024-dim Dense Vector Floats |
| **4. Agent Routing** | User Intent + History | LangGraph Supervisor Router | Atomic Sub-Task Execution List |
| **5. Tool Payload** | Natural Language Params | Pydantic v2 Schema Validator | Typed JSON RPC Payload |
| **6. Output Synthesis**| Raw Agent Results | Reasoning Agent / Claude 3.5 Sonnet | Grounded Markdown with Citations |
| **7. Audit Logging** | Completed Execution Trace | HMAC SHA-256 Signer | Tamper-Evident DB Audit Row |
