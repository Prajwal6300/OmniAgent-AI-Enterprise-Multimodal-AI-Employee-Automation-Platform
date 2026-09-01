# Architecture — Component Architecture & Subsystems

## Status
**Status:** ✅ IMPLEMENTED (Core Subsystems)

---

## 1. Subsystem Decomposition

OmniAgent AI is architected into discrete, modular components that communicate via well-defined internal interfaces, asynchronous event buses, and typed Pydantic contracts.

```mermaid
graph TD
    subgraph Core_Services [FastAPI Core Application Services]
        Auth_Svc[Auth & Security Service]
        Chat_Svc[Conversational Chat Service]
        Doc_Svc[Document Ingestion Service]
        MM_Svc[Multimodal Ingestion Service]
        WF_Svc[Workflow Orchestrator Service]
        Audit_Svc[Tamper-Proof Audit Service]
    end

    subgraph Agent_Subsystems [LangGraph Multi-Agent Cluster]
        Supervisor_Sub[Supervisor Coordinator]
        Worker_Sub[Specialized Workers Swarm]
        Tool_Registry[Typed Tool Registry & Dispatcher]
        State_Engine[Graph State & Memory Manager]
    end

    subgraph Data_Connectors [Database & Storage Adapters]
        DB_Adapter[SQLAlchemy 2.0 Async Session]
        Vector_Adapter[pgvector HNSW Vector Store Adapter]
        Redis_Adapter[Redis Connection Pool & Cache Client]
        S3_Adapter[MinIO / Boto3 Storage Client]
    end

    subgraph Worker_Infrastructure [Asynchronous Execution Fabric]
        Celery_App[Celery Distributed Task Worker]
        Task_Queues[(Redis Priority Message Queues)]
    end

    Chat_Svc --> Supervisor_Sub
    Supervisor_Sub --> Worker_Sub
    Worker_Sub --> Tool_Registry
    Tool_Registry --> DB_Adapter & Vector_Adapter & S3_Adapter

    Doc_Svc --> Task_Queues --> Celery_App
    MM_Svc --> Task_Queues --> Celery_App
    WF_Svc --> Task_Queues --> Celery_App

    Celery_App --> DB_Adapter & Vector_Adapter & S3_Adapter
    Core_Services --> Audit_Svc --> DB_Adapter
```

---

## 2. Key Subsystem Specifications

### 1. Document & Multimodal Ingestion Subsystem (`app.services.ingestion`)
* **Role:** Ingests heterogeneous binary artifacts, validates MIME signatures, computes SHA-256 content hashes for deduplication, and coordinates async Celery worker tasks for OCR, PDF parsing, Whisper speech transcription, and embedding generation.
* **Interfaces:**
  - `IngestDocumentRequest` -> `DocumentID`, `ChunkCount`, `VectorIDs`
  - `PresignedUploadRequest` -> `S3PresignedURL`, `FileKey`

### 2. Multi-Agent Orchestration Subsystem (`app.agents.engine`)
* **Role:** Manages LangGraph state graphs, dynamic agent routing, context injection, short-term conversational working memory, and tool invocation dispatching.
* **State Contract:**
  ```python
  class AgentGraphState(TypedDict):
      session_id: str
      user_id: int
      messages: list[BaseMessage]
      current_task: str
      plan: list[str]
      agent_scratchpad: dict[str, Any]
      active_agent: str
      requires_approval: bool
      pending_action: Optional[dict[str, Any]]
      risk_level: str
      audit_events: list[dict[str, Any]]
  ```

### 3. Tool Registry & Policy Gateway (`app.tools.registry`)
* **Role:** Centralized repository for all executable tools. Each tool is decorated with Pydantic schema validation, permission requirements, risk classification metadata, and execution timeout constraints.
* **Safety Sandbox:** Rejects undeclared kwargs, validates parameter bounds, and logs execution latency.

### 4. Hybrid Vector Retrieval Subsystem (`app.services.rag`)
* **Role:** Coordinates multi-stage retrieval:
  1. Dense vector cosine search against PostgreSQL `pgvector` HNSW index.
  2. Sparse full-text keyword search using PostgreSQL `tsvector` / BM25.
  3. Reciprocal Rank Fusion (RRF) to merge score distributions.
  4. Cross-Encoder reranking (BAAI/bge-reranker-large) to select top-5 relevant chunks.

### 5. Audit & Compliance Ledger (`app.services.audit`)
* **Role:** Intercepts all critical operations and writes immutable JSON log records with HMAC SHA-256 signatures, user IDs, IP addresses, agent IDs, and execution latency.
