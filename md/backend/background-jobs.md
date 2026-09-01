# Backend — Background Jobs & Asynchronous Worker Architecture

## Status
**Status:** ✅ IMPLEMENTED (Celery with Redis Message Broker)

---

## 1. Asynchronous Task Architecture

Heavy computational tasks—such as batch OCR, 500-page PDF ingestion, audio Whisper transcription, vector indexing, and recurring workflow schedules—are offloaded to distributed **Celery Workers** backed by **Redis 7+**.

```mermaid
flowchart TD
    A[FastAPI Gateway / API Route] -->|Enqueues Task| B[(Redis Message Broker: redis://redis:6379/0)]
    
    B --> C{Task Priority Queues}
    
    C -->|high_priority| D[Celery Worker Cluster 1: Real-Time Audio / Actions]
    C -->|default| E[Celery Worker Cluster 2: Multi-Agent Workflows]
    C -->|bulk_ingestion| F[Celery Worker Cluster 3: OCR / PDF Ingestion]
    
    D & E & F --> G[(PostgreSQL & MinIO Object Storage)]
    D & E & F --> H[Task Result Backend: Redis Database 1]
```

---

## 2. Worker Task Catalog

| Task Name | Queue | Retry Policy | Timeout | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`tasks.ingest_document`** | `bulk_ingestion` | 3 retries with exponential backoff | 600s | OCR, PDF extraction, chunking, and embedding generation. |
| **`tasks.transcribe_audio`**| `high_priority` | 2 retries | 180s | Whisper ASR transcription of voice clips. |
| **`tasks.execute_workflow`**| `default` | 3 retries (idempotent) | 300s | Background execution of multi-step DAG workflows. |
| **`tasks.scheduled_health`**| `default` | None | 30s | Periodic Celery Beat heartbeat and vector health verification. |
