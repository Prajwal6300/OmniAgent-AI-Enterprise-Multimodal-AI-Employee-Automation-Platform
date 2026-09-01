# Automation — Event Triggers Specification

## Status
**Status:** ✅ IMPLEMENTED (Webhook, File Upload, Cron, Manual) | 🚧 PARTIALLY IMPLEMENTED (IMAP Email)

---

## 1. Supported Trigger Types

OmniAgent AI workflows can be instantiated by diverse real-time events and scheduled jobs:

| Trigger Type | Source Mechanism | Payload Structure | Use Cases |
| :--- | :--- | :--- | :--- |
| **`file_upload`** | S3 / MinIO Object Storage Event | `{bucket, s3_key, file_size, mime_type}` | Automated invoice processing, resume screening, contract intake. |
| **`webhook`** | External REST HTTP Post | `{source, event_name, payload_data}` | Stripe payment webhooks, Zendesk ticket creation, GitHub push events. |
| **`scheduled_cron`** | Celery Beat / Cron Scheduler | `{schedule_expression, timezone}` | Daily financial reconciliations, nightly database audits, weekly KPI digests. |
| **`manual_api`** | User Web Portal / REST API | `{user_id, prompt, attached_files}` | Interactive ad-hoc AI Employee tasks from the Next.js UI. |
| **`email_inbound`** | IMAP / SendGrid Inbound Parse | `{sender, subject, body_text, attachments}` | Customer support emails, AP billing inbox monitoring. |

---

## 2. Trigger Configuration Schema

```json
{
  "trigger_id": "trig_ap_invoices_01",
  "name": "Vendor Invoice S3 Ingestion Trigger",
  "type": "file_upload",
  "enabled": true,
  "configuration": {
    "bucket": "omni-enterprise-artifacts",
    "prefix": "incoming/invoices/",
    "allowed_extensions": [".pdf", ".png", ".tiff"]
  },
  "workflow_id": "wf_invoice_proc_001"
}
```
