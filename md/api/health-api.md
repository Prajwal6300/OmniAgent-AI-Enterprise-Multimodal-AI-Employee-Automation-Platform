# API — Health, Liveness & Readiness Endpoints (`/api/v1/health`)

## Status
**Status:** ✅ IMPLEMENTED (Kubernetes Probes & Infrastructure Heartbeat)

---

## 1. GET `/api/v1/health`
Returns high-level system status and application version.

* **Method:** `GET`
* **Response (`200 OK`):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "timestamp": "2026-08-15T14:30:00Z"
}
```

---

## 2. GET `/api/v1/health/readiness`
Deep dependency probe verifying database, Redis, MinIO, and ML model connections for container orchestration readiness checks.

* **Method:** `GET`
* **Response (`200 OK`):**
```json
{
  "status": "ready",
  "checks": {
    "postgres_db": { "status": "UP", "latency_ms": 2.1 },
    "pgvector_extension": { "status": "UP", "version": "0.7.0" },
    "redis_cache": { "status": "UP", "latency_ms": 0.8 },
    "s3_object_storage": { "status": "UP" },
    "embedding_model": { "status": "LOADED", "model": "BAAI/bge-large-en-v1.5" }
  }
}
```
