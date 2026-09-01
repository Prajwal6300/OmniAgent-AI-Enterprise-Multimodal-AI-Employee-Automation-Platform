# Product — User Personas & Enterprise Roles Specification

## Status
**Status:** ✅ IMPLEMENTED (6 Granular Roles)

---

## 1. Enterprise User Personas

| Persona Title | Primary Goal | Key Platform Views Used |
| :--- | :--- | :--- |
| **Finance Controller (Manager)** | Verify vendor invoices, ensure 100% 3-way match, authorize payments. | `/approvals`, `/audit`, `/chat` |
| **Accounts Payable Clerk (Operator)**| Upload PDF batches, review extraction results, trigger reconciliations. | `/documents`, `/chat`, `/workflows` |
| **DevOps / IT Engineer (Operator)** | Diagnose stacktraces and screenshots, review automated Jira tickets. | `/chat`, `/documents` |
| **Plant Quality Supervisor (Manager)**| Inspect machinery photos for hairline cracks and approve maintenance work orders. | `/approvals`, `/chat` |
| **Compliance Officer (Auditor)** | Review tamper-proof cryptographic audit trails and verify authorization signatures. | `/audit` |
| **Tenant Administrator (Admin)** | Configure enterprise integrations (SAP, Slack, SMTP), manage users and API keys. | `/settings`, `/workflows` |
