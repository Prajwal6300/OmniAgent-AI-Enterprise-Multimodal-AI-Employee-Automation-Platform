# API — Enterprise REST & Streaming API Reference Overview

## Status
**Status:** ✅ IMPLEMENTED (FastAPI Versioned OpenAPI 3.1 Specification)

---

## 1. Base URL & API Versioning

All API endpoints are versioned under the `/api/v1` namespace:
* **Base URL (Local):** `http://localhost:8000/api/v1`
* **Base URL (Production):** `https://api.omniagent.enterprise.io/api/v1`
* **Interactive OpenAPI Swagger Docs:** `http://localhost:8000/docs`
* **ReDoc Specification:** `http://localhost:8000/redoc`

---

## 2. Global Headers & Authentication

Every authenticated request requires the standard OAuth2 Bearer token:
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
Content-Type: application/json
X-Tenant-ID: <TENANT_UUID> (Optional if bound in JWT)
```

---

## 3. Standard Response Wrapper Schemas

### Standard Success JSON
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "timestamp": "2026-08-15T14:30:00Z",
    "request_id": "req_019283019",
    "execution_time_ms": 28.5
  }
}
```
