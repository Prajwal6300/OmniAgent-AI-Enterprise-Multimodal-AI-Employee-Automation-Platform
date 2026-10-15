# Data Inventory

This document lists every personal data field the OmniAgent AI app collects, stores, processes, or transmits. Policies in this repo must match this inventory exactly.

## 1. User-Account Data (PostgreSQL)

| Table | Field | Type | Storage | Who Can See It | Retention | Purpose |
|---|---|---|---|---|---|---|
| `users` | `email` | `VARCHAR(255)` | PostgreSQL | Org admins, system staff | Until account deletion | Authentication & login |
| `users` | `hashed_password` | `VARCHAR(255)` | PostgreSQL | System staff only (never displayed) | Password verification |
| `users` | `full_name` | `VARCHAR(255)` | PostgreSQL | Org admins, user themselves | Until account deletion | Identity display |
| `users` | `email` | used for `VITE_CONTACT_EMAIL` footer link | Frontend only | Public (if env var set) | Contact purposes |
| `organizations` | `name` | `VARCHAR(255)` | PostgreSQL | Org members, system staff | Until org deletion | Organization identity |
| `organizations` | `slug` | `VARCHAR(100)` | PostgreSQL | Org members, public (via URL) | URL identification |
| `conversations` | `title` | `VARCHAR(255)` | PostgreSQL | Org members, conversation participants | Until deletion | Conversation organization |
| `conversations` | `agent_type` | `VARCHAR(50)` | PostgreSQL | Org members, system staff | AI routing |
| `messages` | `content` | `TEXT` | PostgreSQL | Conversation participants, system staff | Until deletion | User messages |
| `messages` | `sender_type` | `VARCHAR(50)` | PostgreSQL | Conversation participants | Message routing |
| `agent_runs` | `agent_name` | `VARCHAR(100)` | PostgreSQL | Org members, system staff | AI processing audit |
| `agent_runs` | `task_description` | `TEXT` | PostgreSQL | Org members, system staff | AI task logging |
| `agent_runs` | `latency_ms` | `INTEGER` | Postgreformance | System staff | Performance monitoring |
| `agent_runs` | `total_tokens` | `INTEGER` | PostgreSQL | System staff | Cost monitoring |
| `agent_runs` | `cost_usd` | `NUMERIC(10,6)` | PostgreSQL | System staff | Billing/cost tracking |
| `messages` | `citations` | `JSONB` | PostgreSQL | System staff, org members | Source attribution |
| `actions` | `action_type` | `VARCHAR(100)` | PostgreSQL | Org members, system staff | Action classification |
| `actions` | `risk_level` | `VARCHAR(20)` | PostgreSQL | Org members, system staff | Safety categorization |
| `actions` | `input_hash` | `VARCHAR(64)` | PostgreSQL | System staff | Data integrity |
| `actions` | `input_payload` | `JSONB` | PostgreSQL | System staff | Original input (may contain personal data) |
| `actions` | `result_payload` | `JSONB` | PostgreSQL | System staff | Output result |
| `actions` | `error_message` | `TEXT` | PostgreSQL | Org members, system staff | Error reporting |
| `audit_logs` | `event_type` | `VARCHAR(100)` | PostgreSystem staff | Audit trail |
| `audit_logs` | `ip_address` | `VARCHAR(45)` | PostgreSystem staff | System staff | Security logging |
| `audit_logs` | `details` | `JSONB` | PostgreSystem staff | System staff | Event details |
| `notifications` | `title` | `VARCHAR(255)` | PostgreSQL | Notification recipients | Until read/deleted |
| `notifications` | `message` | `TEXT` | PostgreSQL | Notification recipients | Until read/deleted |
| `integrations` | `service_name` | `VARCHAR(100)` | PostgreSQL | Org admins | Third-party connection |
| `integrations` | `config_encrypted` | `TEXT` | PostgreSQL | Org admins only (decrypted) | Integration configuration |

## 2. Frontend Session & State

| Data Type | Source | Storage | Who Can See It | Retention |
|---|---|---|---|---|
| `jwt token` | Login response | `localStorage` (or memory in some configs) | User only (per browser) | Until logout/expire |
| `isAuthenticated` | Auth state | React state | User only | Session |
| `errors` | Form state | React state | User only | Unsubmit/reload |
| `selectedDoc` | Document state | React state | User only | Session |
| `analysisResult` | Analysis state | React state | User only | Session |

## 3. Frontend LocalStorage / Cookies

| Key | Value | Purpose | Expiry |
|---|---|---|---|
| (none found) | - | - | - |

*No localStorage keys or cookies were found in the current frontend code.*

## 4. Form Collection Points

| Form | Fields Collected | Purpose | Legal Basis |
|---|---|---|---|
| `Login` (`/login`) | `email`, `password` | Authentication & access | Contract + consent |
| `Register` (`/register`) | `organization_name`, `admin_email`, `password` | Account creation & tenant setup | Contract + consent |

## 5. Third-Party Data Processors

| Processor | Data Sent | Purpose | Cookie/Storage | Retention |
|---|---|---|---|---|
| `OpenAI` | AI prompts, document content, analysis results | AI document analysis, chat, embeddings | Session-based (no persistent cookies from frontend) | Until user deletes account |
| `Database (PostgreSQL/Neon)` | All user/org/entity records listed above | Persistent storage | Database-level retention policies | Per org policy |
| `Cloudflare R2 / Storage` | Document files, uploads | File storage | Referer/header logging | Per org policy |
| `Hosting (Vercel/Render)` | IP address, session metadata | Web hosting | Server logs | Typically 30-90 days |
| `Analytics (pending)` | Page views, events | Usage measurement | - | - |

## 6. Data Transfers

- **International transfers**: Database runs on cloud infrastructure; data may traverse international networks. No personal data is knowingly transferred outside the EU/India region without safeguards.
- **Data subject access**: Users can request export of their data via the Settings export feature.

## 6. Retention & Deletion

- User data retained until account deletion or organizational policy expiry.
- Audit logs retained for security investigation purposes (duration to be specified in policy).
- Upon deletion: user personal data (email, full_name) anonymized or removed; org-level business data handled per organization admin documentation.

## 7. User Rights

| Right | How to Exercise | Verified By |
|---|---|---|
| Access | Settings → Export My Data | Backend endpoint |
| Correction | Contact via `VITE_CONTACT_EMAIL` | Support ticket |
| Deletion | Settings → Delete My Account | Backend endpoint |
| Withdrawal of consent | Settings → Revoke Consent | Backend endpoint |
| Grievance contact | `VITE_GRIEVANCE_EMAIL` (or `VITE_CONTACT_EMAIL` if not set) | Policy footer |

## 8. Children's Data

- The service is designated for users 18+.
- No knowingly collected data from minors.
- If such data is found, process: delete via Settings or contact `VITE_CONTACT_EMAIL`.

## 9. Security Measures

- Passwords hashed using bcrypt/Argon2 (verify implementation).
- Data in transit encrypted via TLS/HTTPS.
- Data at rest encrypted via PostgreSQL encryption/Cloudflare R2.
- Role-based access control (RBAC) with organization tenant isolation.
- Audit logging of access events.

## 9. Consent Records

- Registration consent: stored with user record, includes policy version timestamp.
- Cookie consent: stored in browser localStorage (to be implemented via cookie banner).
- Age consent: "I am 18 or older" checkbox stored with user record.

*This inventory was generated on `2026-10-15`. Update when fields, services, or retention policies change.*