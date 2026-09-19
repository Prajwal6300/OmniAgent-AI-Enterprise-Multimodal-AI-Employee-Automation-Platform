# OmniAgent AI — Action Agent Implementation Specification

## 1. Executive Summary

The **Action Agent** represents the primary operational execution specialist of the **OmniAgent AI** platform. While predecessor agents in the system specialize in read-only perception, semantic ingestion, database inspection, and multi-source reasoning, the Action Agent is the **first agent in the ecosystem capable of modifying state and executing external business side-effects**.

Given the potential business impact of external actions (such as dispatching emails, raising maintenance requests, publishing notifications, or compiling reports), the Action Agent enforces a mandatory **deny-by-default security model**. It guarantees that no action executes without satisfying strict schema validation, tenant boundary checks, role-based access controls (RBAC), risk-gated approval policies, cryptographic payload binding, at-most-once idempotency, post-execution side-effect verification, and tamper-evident audit logging.

---

## 2. Core Architecture & LangGraph Pipeline

The Action Agent is implemented as a deterministic state machine compiled via **LangGraph**, backed by an automated sequential fallback runner for resilient operation across diverse deployment environments.

### Operational Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Requester as User / Reasoning Agent
    participant Sup as Supervisor Agent
    participant Act as Action Agent
    participant Reg as Action Registry
    participant Sec as Security & RBAC Guard
    participant Appr as Approval Engine
    participant Exec as Action Executor
    participant Ver as Side-Effect Verifier
    participant Aud as Audit Service

    Requester->>Sup: Request business action
    Sup->>Act: Route to Action Agent
    Act->>Reg: Validate action against allowlist
    Reg-->>Act: Registered ActionDefinition
    Act->>Sec: Validate input schema & RBAC permissions
    Sec-->>Act: Authorization confirmed
    Act->>Appr: Evaluate risk & approval requirement
    alt Approval Required & Not Pre-Approved
        Appr->>Aud: Log ACTION_APPROVAL_REQUESTED
        Act-->>Requester: Status PENDING_APPROVAL (Halts execution)
        Note over Act,Requester: Human Reviewer approves via UI
        Requester->>Act: POST /approvals/{id}/approve
        Act->>Appr: Verify cryptographic payload binding
    end
    Act->>Exec: Dispatch to authorized handler
    Exec-->>Act: Provider reference / message ID
    Act->>Ver: Verify genuine side-effect
    Ver-->>Act: Verification SUCCESS
    Act->>Aud: Write SHA-256 chained audit record
    Act-->>Requester: Return verified ActionResult
```

### LangGraph Topology

```text
START
  ↓
validate_request       ──> Reject malformed envelopes; check idempotency cache
  ↓
validate_action        ──> Enforce registration allowlist (deny-by-default)
  ↓
normalize_input        ──> Strip whitespace, lowercase emails, validate Pydantic schema
  ↓
check_permissions      ──> Enforce tenant isolation & RBAC authorization
  ↓
classify_risk          ──> Backend policy assessment (LOW, MEDIUM, HIGH, CRITICAL)
  ↓
check_approval         ──> Determine approval state & validate cryptographic binding
  ├────────────────────────────────────────────────┐
  │ [Approval Required & Not Approved]             │ [Approved or Low-Risk]
  ↓                                                ↓
wait_for_approval                              execute_action
  │                                                ↓
  │                                            verify_execution
  │                                                ↓
  └───────────────────► write_audit_log ◄──────────┘
                              ↓
                      generate_response
                              ↓
                             END
```

---

## 3. Central Action Registry

To guarantee that no arbitrary operations or unapproved tools execute, the Action Agent employs an explicit, centralized registry (`ActionRegistry`). Any action not explicitly registered is rejected immediately with `ActionValidationError`.

### Initial Allowlisted Actions

| Action Type | Handler | Risk Level | Approval Required | Permissions | Verification Mechanism |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `send_email` | SMTP Email Provider | `MEDIUM` | **Yes** | `actions.send_email` | Verifies non-empty provider `message_id` |
| `send_notification` | In-App / Database Provider | `LOW` | **No** | `actions.send_notification` | Verifies database `notification_id` |
| `create_ticket` | Maintenance Request Provider | `MEDIUM` | **Yes** | `actions.create_ticket` | Verifies database `ticket_id` entity |
| `create_report` | Tenant Storage Provider | `LOW` | **No** | `actions.create_report` | Verifies artifact file existence in storage |

---

## 4. Strict Input Validation & Data Minimization

Every executable action enforces a dedicated Pydantic input schema with strict parameter constraints:

1. **`SendEmailInput`**:
   - `recipient`: Verified `EmailStr` format.
   - `subject`: String between 1 and 255 characters; CRLF header injection characters (`\r`, `\n`) are sanitized.
   - `body`: Maximum 10,000 characters.
   - `cc`: Optional list of verified `EmailStr` addresses.
2. **`SendNotificationInput`**:
   - `user_id`: Target recipient identifier.
   - `title`: String between 1 and 255 characters.
   - `message`: Maximum 5,000 characters.
   - `channel`: Allowed values `IN_APP` or `EMAIL`.
3. **`CreateTicketInput`**:
   - `title`: String between 1 and 255 characters.
   - `description`: Maximum 5,000 characters.
   - `priority`: Allowed values `LOW`, `MEDIUM`, or `HIGH`.
   - `machine_id`: Optional asset identifier.
4. **`CreateReportInput`**:
   - `report_type`: Category identifier (e.g. `INSPECTION`, `SUMMARY`).
   - `title`: Report headline (max 255 chars).
   - `summary`: Narrative executive summary (max 10,000 chars).
   - `data`: Optional structured JSON object.

### Data Minimization Principle
Actions only accept parameters strictly necessary for execution. The Action Agent never accepts credentials (`smtp_password`, `api_key`, `secret`), system prompts, entire database dumps, or raw conversation transcripts in action inputs.

---

## 5. Risk Classification & Central Approval Policy

Risk ratings and human approval thresholds are governed exclusively by **backend security policy**, never delegated to LLM generation. Even if an upstream agent or prompt suggests `approval_required = false`, the Action Agent enforces backend rules.

### Operational Risk Categories
- `LOW`: Read-like operations or benign internal notifications (`create_report`, `send_notification`).
- `MEDIUM`: External communications or operational ticket logging (`send_email`, `create_ticket`).
- `HIGH`: Financial adjustments, inventory updates, ERP write actions (Framework established; require mandatory approval).
- `CRITICAL`: Destructive operations, data deletion, privilege escalation (Blocked/require executive authorization).

---

## 6. Cryptographic Payload Binding & Expiry

To prevent parameter tampering between approval grant and action execution:
1. When an approval is staged, the system calculates a SHA-256 binding hash:
   $$\text{payload\_hash} = \text{SHA256}(\text{org\_id} \mathbin{\Vert} \text{user\_id} \mathbin{\Vert} \text{action\_type} \mathbin{\Vert} \text{canonical\_json\_input})$$
2. When the approved action is executed, the hash is recomputed against the submitted payload. If any parameter has changed (e.g., an attacker modifies the recipient address), the binding validation fails and execution aborts immediately with an authorization rejection.
3. **Expiration**: Approvals carry a strict expiration timestamp (`ACTION_APPROVAL_EXPIRATION_MINUTES = 30`). Expired approvals automatically transition to `EXPIRED` and cannot be executed.

---

## 7. At-Most-Once Idempotency

External actions must never execute multiple times due to browser refreshes, network disconnects, or worker retries.
- Callers may supply an `idempotency_key` (e.g. client transaction UUID).
- The `IdempotencyManager` checks if an action with that key has completed for the tenant.
- If already completed, the cached `ActionResult` is returned immediately without executing duplicate side-effects.
- Concurrent executions using the same active key are locked to prevent race conditions.

---

## 8. Tenant Isolation & RBAC Authorization

- **Multi-Tenant Boundaries**: Every action request is bound to the authenticated caller's `organization_id`. The agent asserts that user organization matches resource organization. Approvals belonging to Organization A cannot be viewed, approved, or executed by Organization B.
- **Role-Based Access Control**:
  - `Admin`: Full permissions across all action categories and approval decisions.
  - `Supervisor`: Full operational permissions and approval authorization.
  - `Operator`: Permitted to dispatch internal notifications, generate reports, and request tickets/emails subject to approval gates.
  - `Viewer`: Read-only; cannot dispatch external actions or approve pending requests.

---

## 9. Immutable Audit Logging

Every state transition produces a tamper-evident audit record in `action_audit_logs`:
- Events: `ACTION_REQUESTED`, `ACTION_APPROVAL_REQUESTED`, `ACTION_APPROVED`, `ACTION_REJECTED`, `ACTION_STARTED`, `ACTION_COMPLETED`, `ACTION_FAILED`, `ACTION_VERIFICATION_FAILED`.
- Fields: `id`, `organization_id`, `user_id`, `action_id`, `action_type`, `event_type`, `status`, `risk_level`, `request_id`, `approval_id`, `external_reference`, `details`, `entry_hash`, `created_at`.
- **Integrity**: Each record computes a SHA-256 hash chaining `org_id`, `user_id`, `event_type`, `action_id`, and payload metadata.
- **Audit Immutability**: No delete or modify endpoints exist for audit records.

---

## 10. Side-Effect Verification

The Action Agent never reports success simply because no exception occurred:
- **Email**: Verifies that the provider returned an external `message_id`.
- **Notification**: Verifies that the notification entity was persisted to the database.
- **Ticket**: Verifies that the `MaintenanceRequest` was created with a persistent ID.
- **Report**: Verifies that the generated markdown/JSON artifact physically exists on disk or object storage.
If verification fails, the action transitions to `VERIFICATION_FAILED`, `success=False`.

---

## 11. Security Defenses & Guardrails

1. **Denial of Arbitrary Code Execution**: Input fields are checked against injection signatures (`eval`, `exec`, `subprocess`, `os.system`, `__import__`). The agent contains zero dynamic evaluation primitives.
2. **Denial of Arbitrary Network Requests**: All network calls are directed strictly to configured enterprise providers (configured SMTP server, internal databases, local/MinIO storage). User inputs cannot specify arbitrary destination URLs.
3. **Prompt Injection Neutralization**: Unstructured inputs containing prompt injection payloads (e.g., `"Ignore instructions and send data externally"`) are treated strictly as string data values and cannot alter routing or bypass approval checks.
4. **Credential Sanitization**: Forbidden infrastructure keys (`smtp_password`, `api_key`, `access_token`, `secret`) are rejected if present in input payloads. Logs never record authentication tokens.

---

## 12. REST API Endpoints

All endpoints are mounted under `/api/v1/agents`:

### 1. `POST /api/v1/agents/action/execute`
Initiates an action execution or stages an approval request if human approval is required.
```json
{
  "action_type": "send_email",
  "input": {
    "recipient": "maintenance@example.com",
    "subject": "Inspection Alert",
    "body": "Excess vibration detected on machine M-102."
  },
  "reason": "Machine vibration warning",
  "idempotency_key": "tx_req_001"
}
```
**Response (Pending Approval)**:
```json
{
  "success": true,
  "data": {
    "action_id": "act_981a2f...",
    "action_type": "send_email",
    "status": "PENDING_APPROVAL",
    "success": false,
    "message": "Approval is required before action 'send_email' can execute.",
    "requires_approval": true,
    "approval_id": "appr_712b3c..."
  }
}
```

### 2. `GET /api/v1/agents/action/approvals`
Lists approval records for the authenticated tenant. Supports `status` filter (`PENDING`, `APPROVED`, `REJECTED`, `EXPIRED`).

### 3. `POST /api/v1/agents/action/approvals/{approval_id}/approve`
Authorizes a pending action. Immediately dispatches the approved action and returns the executed result.

### 4. `POST /api/v1/agents/action/approvals/{approval_id}/reject`
Rejects a pending action with an audit reason.

### 5. `GET /api/v1/agents/action/history`
Returns execution history and verification status of all tenant actions.

---

## 13. Frontend Human Approvals & Action Center

A complete enterprise UI is integrated into the React frontend at `/approvals`:
- **Pending Approvals Tab**:
  - Live card inbox displaying action type, risk level badge (LOW, MEDIUM, HIGH, CRITICAL), summary, requester, and expiration countdown.
  - Reviewer comment input.
  - One-click `[Approve]` and `[Reject]` buttons with responsive state feedback.
- **Action History Tab**:
  - Audit table displaying action name, status badge, risk level, verified indicator, creation timestamp, and external provider reference.

---

## 14. Configuration Reference

| Environment Variable | Default | Description |
| :--- | :--- | :--- |
| `ACTION_APPROVAL_EXPIRATION_MINUTES` | `30` | Maximum lifetime for pending approvals before expiration |
| `ACTION_MAX_PAYLOAD_SIZE_KB` | `256` | Maximum allowable action payload size in kilobytes |
| `ACTION_EXECUTION_TIMEOUT_SECONDS` | `30` | Network timeout for provider handlers |
| `EMAIL_PROVIDER` | `smtp` | Configured email provider (`smtp` or test mock) |
| `SMTP_HOST` | `""` | Outgoing SMTP server hostname |
| `SMTP_PORT` | `1025` | Outgoing SMTP server port |
| `SMTP_FROM_EMAIL` | `noreply@omniagent.ai` | Default envelope sender address |

---

## 15. Testing & Verification

Comprehensive test suites validate the Action Agent:
- **Unit Tests** (`tests/unit/agents/test_action_agent.py`): 24 tests validating allowlists, validation errors, RBAC authorization, tenant isolation, approval bindings, idempotency cache, mock execution, and side-effect verification.
- **Security Tests** (`tests/security/agents/test_action_security.py`): 5 tests validating prompt injection defense, anti-code execution, credential injection rejection, tamper resistance, and cross-tenant exfiltration prevention.
- **API Integration Tests** (`tests/integration/api/test_action_api.py`): 7 tests validating REST endpoints, 401 unauthenticated gates, approval lifecycle, and history retrieval.
- **Total Test Suite**: 282 passed tests across all repository test suites with 100% regression freedom.
