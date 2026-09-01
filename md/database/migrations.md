# Database — Alembic Migrations & Schema Evolution

## Status
**Status:** ✅ IMPLEMENTED (Alembic Version-Controlled Migrations)

---

## 1. Migration Management Workflow

Database schema evolution is managed via **Alembic**. All table modifications, column additions, and index updates must be written as reversible migration scripts.

```bash
# Generate a new migration after updating SQLAlchemy models
alembic revision --autogenerate -m "add_human_approvals_table"

# Apply all pending migrations to the database
alembic upgrade head

# Rollback the last migration
alembic downgrade -1
```

---

## 2. Migration History Timeline

| Revision ID | Migration Name | Applied Date | Description |
| :--- | :--- | :--- | :--- |
| **`0001_initial`** | Initial Core Schema | 2026-08-01 | Created `tenants`, `users`, `chat_sessions`, and `chat_messages`. |
| **`0002_pgvector`** | Enable pgvector & Documents | 2026-08-05 | Enabled `vector` extension, created `documents` and `document_chunks`. |
| **`0003_workflows`**| Workflow Engine & Approvals | 2026-08-10 | Created `workflows`, `workflow_runs`, and `human_approvals`. |
| **`0004_audit_hmac`**| Immutable Audit Ledger | 2026-08-15 | Created `audit_logs` table with HMAC signature columns. |
