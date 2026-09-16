# OmniAgent AI — Database Agent

The **Database Agent** enables enterprise users to query authorized business data using natural language. It enforces zero-trust validation, strict multi-tenant isolation, approved schema allowlists, and parameterized read-only SQL generation.

---

## Key Principles & Guardrails

1. **Zero-Trust LLM Access**: The LLM is never granted raw database credentials or direct database execution rights.
2. **Strictly Read-Only**: Only `SELECT` statements are permitted. `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, and administrative statements are unconditionally rejected.
3. **Multi-Tenant Isolation**: Every query accessing business tables must enforce `organization_id = :organization_id` bound to the authenticated user's organization.
4. **Controlled Schema Registry**: The agent only discovers and operates upon explicitly allowlisted tables and columns. Passwords, secrets, and system tables are never exposed.
5. **Parameterized Queries**: All user-supplied literals and filters are strictly parameterized to eliminate SQL injection.
6. **Bounded Resource Usage**: Bounded timeouts (`DATABASE_AGENT_QUERY_TIMEOUT_SECONDS`) and row limits (`DATABASE_AGENT_MAX_ROWS`) protect against runaway queries.

---

## LangGraph Workflow Architecture

```
START
  │
  ▼
validate_request       ──(Invalid/Refusal)──► validate_response ──► END
  │
  ▼
identify_data_intent
  │
  ▼
inspect_schema         ──(No Match)─────────► validate_response ──► END
  │
  ▼
generate_query_plan
  │
  ▼
generate_sql           ──(Failure)──────────► validate_response ──► END
  │
  ▼
validate_sql           ──(Violation)────────► validate_response ──► END
  │
  ▼
enforce_tenant_filter  ──(Violation)────────► validate_response ──► END
  │
  ▼
execute_query          ──(Timeout/Error)────► validate_response ──► END
  │
  ▼
summarize_results
  │
  ▼
validate_response
  │
  ▼
 END
```

---

## API Endpoint

- **Endpoint**: `POST /api/v1/agents/database/query`
- **Authentication**: Bearer JWT token required
- **Payload**:
  ```json
  {
    "question": "How many pending orders do we have?",
    "limit": 20
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "data": {
      "question": "How many pending orders do we have?",
      "summary": "There are 2 pending orders.",
      "columns": ["pending_orders_count"],
      "rows": [{"pending_orders_count": 2}],
      "row_count": 1,
      "query_executed": true,
      "confidence": 0.98,
      "limited": false
    }
  }
  ```
