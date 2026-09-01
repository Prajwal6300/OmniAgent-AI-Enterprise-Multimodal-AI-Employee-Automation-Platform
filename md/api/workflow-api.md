# API — Workflow Automation Endpoints (`/api/v1/workflows`)

## Status
**Status:** ✅ IMPLEMENTED (Workflow CRUD, Run Triggers & Status)

---

## 1. POST `/api/v1/workflows`
Registers a new declarative workflow DAG.

* **Method:** `POST`
* **Request:**
```json
{
  "name": "Vendor Invoice Reconcile & SAP Post",
  "description": "Automated 3-way matching workflow",
  "dag_definition": {
    "trigger": { "type": "file_upload" },
    "nodes": [ ... ],
    "edges": [ ... ]
  }
}
```

* **Response (`201 Created`):** `{ "success": true, "data": { "workflow_id": "wf_991823" } }`

---

## 2. POST `/api/v1/workflows/{id}/trigger`
Manually instantiates an execution run of a registered workflow.

* **Method:** `POST`
* **Request:** `{ "input_payload": { "s3_key": "ten_001928/invoices/inv_9912.pdf" } }`
* **Response (`202 Accepted`):**
```json
{
  "success": true,
  "data": {
    "run_id": "run_88192039",
    "status": "RUNNING",
    "started_at": "2026-08-15T14:30:00Z"
  }
}
```
