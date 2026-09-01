# API — Human Approval Endpoints (`/api/v1/approvals`)

## Status
**Status:** ✅ IMPLEMENTED (Pending Queue, Approval/Rejection & Signatures)

---

## 1. GET `/api/v1/approvals/pending`
Fetches all currently suspended high-risk tasks requiring human authorization.

* **Method:** `GET`
* **Response (`200 OK`):**
```json
{
  "success": true,
  "data": [
    {
      "approval_id": "appr_771829",
      "workflow_run_id": "run_88192039",
      "task_name": "Post AP Invoice Payment to SAP",
      "risk_level": "HIGH",
      "created_at": "2026-08-15T14:32:00Z",
      "payload": {
        "invoice_id": "INV-2026-8812",
        "amount": 14250.00,
        "vendor": "Apex Precision"
      }
    }
  ]
}
```

---

## 2. POST `/api/v1/approvals/{id}/decide`
Submits an authorized operator's decision (Approve or Reject) to resume or cancel the suspended workflow DAG.

* **Method:** `POST`
* **Request:**
```json
{
  "decision": "APPROVED", // "APPROVED" | "REJECTED"
  "reason": "Verified purchase order match with vendor agreement.",
  "modified_payload": null
}
```

* **Response (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "approval_id": "appr_771829",
    "status": "APPROVED",
    "resumed_workflow_run_id": "run_88192039",
    "audit_record_id": "audit_log_991823"
  }
}
```
