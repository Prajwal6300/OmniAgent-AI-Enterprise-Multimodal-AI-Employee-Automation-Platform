# Workflows — Automated 3-Way Invoice Matching & ERP Posting

## Status
**Status:** ✅ IMPLEMENTED (Production End-to-End Workflow)

---

## 1. Workflow Architecture & Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Vendor as Vendor / AP Clerk
    participant Engine as Workflow DAG Engine
    participant DocAg as Document Agent
    participant DBAg as Database Agent
    participant ReasAg as Reasoning Agent
    participant Gate as Human Approval Gate
    participant ActAg as Action Agent (SAP ERP)
    participant Slack as Slack Channel

    Vendor->>Engine: Uploads Invoice PDF (INV-2026-8812)
    Engine->>DocAg: Parse & Extract Structured JSON
    DocAg-->>Engine: Invoice Line Items, Vendor "Apex Precision", Total $14,250.00
    
    Engine->>DBAg: Fetch PO-9014 and Goods Receipt GR-9021
    DBAg-->>Engine: PO Terms ($14,250.00, 4 Server Racks, 8 PDUs)
    
    Engine->>ReasAg: Perform 3-Way Match & Variance Math
    ReasAg-->>Engine: 100% Match Confirmed (Variance 0.00%); High Risk Flagged (> $10k)
    
    Engine->>Gate: Suspend Workflow & Notify Approver
    Gate->>Slack: Post Interactive Approval Card to #finance-approvals
    
    actor Manager as Finance Manager
    Manager->>Gate: Click "Authorize & Post" in Next.js Portal
    Gate-->>Engine: Resumes DAG with Cryptographic Signature
    
    Engine->>ActAg: Post Journal Entry to SAP ERP (REST API)
    ActAg-->>Engine: HTTP 201 Created (SAP Doc #SAP-DOC-2026-099412)
    
    Engine->>Slack: Broadcast Posting Confirmation
```

---

## 2. Straight-Through Processing (STP) Policies

* **Invoices $\le \$1,000$ USD with 0.00% Variance:** Auto-executed immediately into ERP with `LOW` risk audit logging (100% STP).
* **Invoices $>\$1,000$ or Variance $>0.5\%$:** Suspended for manager digital signature.
