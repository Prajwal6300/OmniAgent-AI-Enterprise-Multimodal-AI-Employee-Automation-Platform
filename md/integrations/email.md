# Integrations — Email Connectors (SMTP, IMAP & SendGrid)

## Status
**Status:** ✅ IMPLEMENTED (Outbound SMTP & SendGrid API) | 🚧 PARTIALLY IMPLEMENTED (Inbound IMAP Polling)

---

## 1. Outbound & Inbound Email Capabilities

* **Outbound Delivery (SMTP / SendGrid):** Dispatches automated PDF reports, human approval request notices, and customer support responses with HTML/plain-text multipart MIME support.
* **Inbound Ingestion (IMAP / Webhook):** Monitors dedicated corporate mailboxes (e.g., `invoices@company.com`), extracts attached PDFs/receipts, and triggers the invoice reconciliation workflow.

---

## 2. Configuration Parameters

```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<YOUR_SENDGRID_API_KEY>
SMTP_FROM_EMAIL=notifications@omniagent.enterprise.io
SMTP_TLS=true
```
