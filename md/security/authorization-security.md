# Security — Authorization Security & Multi-Tenant Isolation

## Status
**Status:** ✅ IMPLEMENTED (Row-Level Security & Tenant Scoping)

---

## 1. Multi-Tenant Data Isolation Strategy

OmniAgent AI enforces strict **Logical Multi-Tenancy** across all relational tables, vector stores, object storage paths, and in-memory caches.

```mermaid
flowchart TD
    A[Incoming Request with JWT] --> B[Extract tenant_id & role from Verified Token]
    
    B --> C[PostgreSQL Session Hook: Set Local tenant_id]
    
    C --> D[Relational Query Execution: Auto-inject WHERE tenant_id = :tenant_id]
    C --> E[pgvector Search: Auto-inject WHERE tenant_id = :tenant_id]
    C --> F[S3 Storage Access: Restrict Prefix to s3://bucket/{tenant_id}/*]
    
    D & E & F --> G[Strict Zero-Data-Leakage Isolation]
```

---

## 2. Row-Level Security Policies (PostgreSQL)

```sql
-- Enable Row Level Security on core enterprise tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Enforce tenant isolation policy
CREATE POLICY tenant_isolation_documents ON documents
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY tenant_isolation_chunks ON document_chunks
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```
