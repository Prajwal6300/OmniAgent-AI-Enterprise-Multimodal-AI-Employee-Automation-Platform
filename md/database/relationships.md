# Database — Entity Relationships & Mermaid ER Diagrams

## Status
**Status:** ✅ IMPLEMENTED (Foreign Key Constraints & Cascading Rules)

---

## 1. Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    TENANTS ||--o{ USERS : "has many"
    TENANTS ||--o{ DOCUMENTS : "owns"
    TENANTS ||--o{ WORKFLOWS : "configures"
    TENANTS ||--o{ CHAT_SESSIONS : "owns"
    TENANTS ||--o{ AUDIT_LOGS : "logs"

    USERS ||--o{ CHAT_SESSIONS : "creates"
    USERS ||--o{ WORKFLOW_RUNS : "triggers"
    USERS ||--o{ HUMAN_APPROVALS : "decides"

    DOCUMENTS ||--o{ DOCUMENT_CHUNKS : "contains"

    CHAT_SESSIONS ||--o{ CHAT_MESSAGES : "contains"

    WORKFLOWS ||--o{ WORKFLOW_RUNS : "executes"
    WORKFLOW_RUNS ||--o{ HUMAN_APPROVALS : "spawns"

    TENANTS {
        uuid id PK
        string name
        string slug
    }

    USERS {
        uuid id PK
        uuid tenant_id FK
        string email
        string role
    }

    DOCUMENTS {
        uuid id PK
        uuid tenant_id FK
        string title
        string status
    }

    DOCUMENT_CHUNKS {
        uuid id PK
        uuid document_id FK
        vector embedding
        text content
    }

    CHAT_SESSIONS {
        uuid id PK
        uuid user_id FK
        string title
    }

    CHAT_MESSAGES {
        uuid id PK
        uuid session_id FK
        string role
        text content
    }

    WORKFLOWS {
        uuid id PK
        uuid tenant_id FK
        jsonb dag_definition
    }

    WORKFLOW_RUNS {
        uuid id PK
        uuid workflow_id FK
        string status
    }

    HUMAN_APPROVALS {
        uuid id PK
        uuid workflow_run_id FK
        string risk_level
        string status
    }

    AUDIT_LOGS {
        uuid id PK
        uuid tenant_id FK
        string event_type
        string hmac_signature
    }
```

---

## 2. Foreign Key & Cascade Deletion Rules

* **`ON DELETE CASCADE`:** Applied to `document_chunks`, `chat_messages`, and `workflow_runs` when their parent entities (`documents`, `chat_sessions`, `workflows`) are deleted.
* **`ON DELETE SET NULL`:** Applied to `user_id` references in `audit_logs` and `workflow_runs` to preserve historical audit logs even if a user account is removed.
