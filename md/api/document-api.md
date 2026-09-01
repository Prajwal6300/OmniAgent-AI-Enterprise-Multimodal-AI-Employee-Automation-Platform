# API — Document Ingestion & Knowledge Endpoints (`/api/v1/documents`)

## Status
**Status:** ✅ IMPLEMENTED (Presigned Uploads, Ingestion Queue & Vector Status)

---

## 1. POST `/api/v1/documents/presigned`
Generates a presigned S3/MinIO upload URL for direct multipart client binary uploads.

* **Method:** `POST`
* **Request:**
```json
{
  "filename": "Global_Travel_Policy_2026.pdf",
  "mime_type": "application/pdf",
  "file_size_bytes": 4518290
}
```

* **Response (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "document_id": "doc_991823-110",
    "s3_key": "ten_001928/documents/doc_991823-110/Global_Travel_Policy_2026.pdf",
    "upload_url": "http://minio:9000/omni-enterprise-artifacts/ten_001928/documents/doc_991823-110/Global_Travel_Policy_2026.pdf?X-Amz-Algorithm=...",
    "expires_in_seconds": 900
  }
}
```

---

## 2. POST `/api/v1/documents/ingest`
Enqueues a background Celery worker task to OCR, parse, chunk, and index the uploaded S3 document into `pgvector`.

* **Method:** `POST`
* **Request:** `{ "document_id": "doc_991823-110", "category": "hr_policy" }`
* **Response (`202 Accepted`):**
```json
{
  "success": true,
  "data": {
    "task_id": "celery_task_88192031",
    "status": "PROCESSING",
    "message": "Document ingestion enqueued."
  }
}
```
