# OmniAgent AI — Enterprise Security & Compliance Specification

## 1. Multi-Tenancy & Data Isolation

1. **Foreign Key Scoping**: Every core tenant table contains a mandatory non-nullable `organization_id` foreign key with `ON DELETE CASCADE`.
2. **Database Query Level**: All SQLAlchemy query builders and database repositories mandate an explicit `organization_id` filter. Cross-tenant access attempts immediately fail with HTTP 403 Forbidden or 404 Not Found.
3. **Storage Scoping**: Supabase Object Storage paths follow the strictly enforced format `organizations/{org_id}/documents/{document_id}/{filename}`. Path traversal attempts (`../`) are detected and rejected.
4. **pgvector Isolation**: Dense cosine similarity vector queries enforce `WHERE organization_id = :org_id` before computing similarity ranking.

---

## 2. Role-Based Access Control (RBAC)

The platform enforces a strict 6-tier role hierarchy with discrete permissions:

| Role | Hierarchy | Permitted Operations |
|---|---|---|
| **Owner** | Tier 6 (Highest) | Full organization administration, member deletion, billing |
| **Admin** | Tier 5 | User management, integration configuration, team invitations |
| **Supervisor** | Tier 4 | Human-in-the-loop authorization, approving pending actions |
| **Operator** | Tier 3 | Executing multi-agent workflows, uploading documents, running chat |
| **Auditor** | Tier 2 | Verifying cryptographic audit chains, trace inspection |
| **Viewer** | Tier 1 (Lowest) | Read-only inspection of reports and analytics |

---

## 3. Cryptographic Tamper-Proof Audit Chaining

All operational side-effects (database mutations, ticket creation, email dispatch) generate an immutable audit log entry in `audit_logs` and `action_audit_logs`:
- **Chaining Mechanism**: Each record stores `prev_hash` (the SHA-256 hash of the previous log entry).
- **Current Hash Calculation**:
  $$\text{entry\_hash} = \text{SHA256}(\text{prev\_hash} \,||\, \text{timestamp} \,||\, \text{canonical\_payload})$$
- **Verification Script**: Independent offline script `scripts/verify_audit_chain.py` validates the entire hash chain from the genesis block forward. Any row tampering, deletion, or reordering breaks the chain immediately.

---

## 4. Human-in-the-Loop Approval & Idempotency

Actions are classified into 4 risk tiers: `LOW`, `MEDIUM`, `HIGH`, and `CRITICAL`.
- **High/Critical Gating**: High and Critical actions cannot execute without supervisor approval.
- **Dual Approver Requirement**: `CRITICAL` risk operations (e.g. data wipes, global configurations) require approval by two distinct authorized supervisors.
- **HMAC Payload Binding**: The approval token binds cryptographically to the canonical JSON representation of the action parameters using HMAC-SHA256. If parameters are altered between approval and execution, validation fails.
- **Distributed Locking**: Approvals utilize Redis distributed locks to prevent race conditions or duplicate execution runs.

---

## 5. Input Validation & Prompt Injection Defense

1. **SQL Agent Defense**: All generated SQL queries pass through strict AST analysis via `sqlglot`:
   - Only `SELECT` statements are permitted.
   - All DDL (`DROP`, `ALTER`, `CREATE`) and DML (`INSERT`, `UPDATE`, `DELETE`) are blocked.
   - Access to PostgreSQL system tables (`pg_*`, `information_schema`) is prohibited.
   - A mandatory tenant filter matching the current request's `organization_id` is enforced.
2. **Direct Prompt Injection Guard**: Inputs are scanned using multi-pattern heuristic evaluators for system prompt exfiltration, instruction overrides, or delimiters.
3. **File Upload Verification**: Files are validated against magic bytes (libmagic / byte signatures) and size caps (25 MB) before parsing.
