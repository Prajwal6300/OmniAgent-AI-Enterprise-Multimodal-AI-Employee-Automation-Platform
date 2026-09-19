# OmniAgent AI — Action Agent

The **Action Agent** is the cognitive execution specialist responsible for executing authorized enterprise side-effects across external and internal systems.

As the first agent in the OmniAgent AI platform capable of modifying state and executing business side-effects, the Action Agent enforces mandatory:
- **Deny-by-default security posture**
- **Strict tenant boundary isolation**
- **Fine-grained RBAC permission checks**
- **Mandatory human-in-the-loop (HITL) approval gates** for medium and high-risk operations
- **Cryptographic approval payload binding** (SHA-256) to prevent tampering
- **At-most-once idempotency guarantees**
- **Independent post-execution side-effect verification**
- **Tamper-evident, immutable audit trails**
- **Anti-arbitrary code execution & anti-data-exfiltration defenses**

---

## Architecture & Workflow

```text
User / Reasoning Agent
         ↓
  Supervisor Agent
         ↓
    Action Agent
         ↓
  [1. validate_request]      ──> Deny unknown or malformed envelopes
         ↓
  [2. validate_action]       ──> Verify against explicit registration allowlist
         ↓
  [3. normalize_input]       ──> Pydantic schema validation & parameter normalization
         ↓
  [4. check_permissions]     ──> Enforce tenant & RBAC permissions
         ↓
  [5. classify_risk]         ──> LOW, MEDIUM, HIGH, or CRITICAL rating
         ↓
  [6. check_approval]        ──> Deterministic backend policy evaluation
       /         \
 [Approved]   [Pending Approval]
    /                \
   /            [7. wait_for_approval]  ──> Create ActionApproval & stop execution
  ↓
[8. execute_action]          ──> Dispatch to authorized provider handler
  ↓
[9. verify_execution]        ──> Confirm provider message ID / database row / storage artifact
  ↓
[10. write_audit_log]        ──> Save SHA-256 chained audit record
  ↓
[11. generate_response]      ──> Return verified ActionResult to caller
```

---

## Supported Action Allowlist

| Action Identifier | Category | Default Risk | Approval Required | Handlers / Integrations | Required Permission |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `send_email` | External Communication | `MEDIUM` | **Yes** | SMTP Email Provider | `actions.send_email` |
| `send_notification` | Internal Dispatch | `LOW` | **No** | In-App / Database Notification | `actions.send_notification` |
| `create_ticket` | Operations / Maintenance | `MEDIUM` | **Yes** | MaintenanceRequest Ticket Provider | `actions.create_ticket` |
| `create_report` | Reporting / Storage | `LOW` | **No** | Local / S3 Storage Service Provider | `actions.create_report` |

---

## Cryptographic Approval Binding

When an action requires approval, the system calculates a SHA-256 payload binding hash:
```python
payload_hash = sha256(f"{org_id}:{user_id}:{action_type}:{canonical_json_input}")
```
If an approved action request is later executed with modified or tampered parameters, the hash verification fails and execution is immediately rejected.
All approvals automatically expire after the configured window (default: 30 minutes).

---

## Testing & Deterministic Mocks

The Action Agent includes deterministic fake providers for fast, reliable unit and security testing without real external infrastructure:
- `FakeEmailProvider`
- `FakeNotificationProvider`
- `FakeTicketProvider`
- `FakeReportProvider`
