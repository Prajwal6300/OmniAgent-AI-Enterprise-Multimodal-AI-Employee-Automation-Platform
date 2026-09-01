# Frontend — Page Routes & View Specifications

## Status
**Status:** ✅ IMPLEMENTED (All Core Enterprise Dashboard Views)

---

## 1. Route Hierarchy

| Route Path | Layout Type | Access Level | Description |
| :--- | :--- | :--- | :--- |
| **`/login`** | Auth Center Card | Public | Email/password login with MFA and error handling. |
| **`/chat`** | Split Workspace | All Authenticated | Main AI Employee conversational interface with document viewer sidecar. |
| **`/approvals`** | Master-Detail Queue | Manager, Admin | Human-in-the-loop pending approval inbox with diff reviewer. |
| **`/workflows`** | Data Table + Modal | Operator, Admin | List of configured workflow DAGs and trigger logs. |
| **`/documents`** | Grid & List View | All Authenticated | Enterprise knowledge base manager and vector indexing status. |
| **`/audit`** | Searchable Table | Auditor, Admin | Immutable audit log viewer with cryptographic signature verifier. |
| **`/settings`** | Tabbed Form View | Admin | Organization settings, API keys, and RBAC role assignments. |

---

## 2. Key View Specifications

### 1. `/chat` (AI Employee Workspace)
* **Left Panel:** Conversational message history, streaming tokens, multi-agent thought accordions, and inline source citation chips.
* **Right Panel (Sidecar):** Dynamic context viewer—displays uploaded PDFs with highlighted text spans, machinery photos with bounding box overlays, or spreadsheet dataframes.

### 2. `/approvals` (Human Approval Center)
* Displays high-risk suspended tasks with risk badges (`HIGH`, `MEDIUM`), requested ERP mutation parameters, and single-click **Approve**, **Reject**, or **Edit & Approve** controls.
