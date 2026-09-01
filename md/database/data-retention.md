# Database — Data Retention, Partitioning & Archival Policies

## Status
**Status:** ✅ IMPLEMENTED (Declarative Retention Rules & Soft Deletes)

---

## 1. Enterprise Data Retention Matrix

| Data Entity | Active DB Retention | Archival Storage | Permanent Purge Policy |
| :--- | :--- | :--- | :--- |
| **Audit Logs (`audit_logs`)** | 365 Days | Encrypted S3 Glacier (7 Years) | Compliance-governed; immutable. |
| **Chat Sessions (`chat_sessions`)**| 90 Days | Compressed JSON in S3 | Purged after 365 days unless tagged. |
| **Workflow Runs (`workflow_runs`)** | 60 Days | Cold S3 Storage | Purged after 180 days. |
| **Document Chunks (`document_chunks`)**| Active Lifetime | S3 Vector Snapshot | Purged immediately upon document deletion. |

---

## 2. Table Partitioning Strategy (Audit Logs)

The `audit_logs` table is partitioned by range on the `created_at` timestamp column to ensure high write throughput and painless historical drops:
```sql
CREATE TABLE audit_logs (
    id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    -- additional columns ...
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Monthly partition examples
CREATE TABLE audit_logs_2026_08 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-08-01 00:00:00+00') TO ('2026-09-01 00:00:00+00');
```
