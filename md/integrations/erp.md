# Integrations — ERP Connectors (SAP S/4HANA, Oracle & Custom REST)

## Status
**Status:** 🚧 PARTIALLY IMPLEMENTED (Generic REST ERP Connector Active; SAP RFC Adapter in Progress)

---

## 1. Enterprise ERP Connector Framework

OmniAgent AI interfaces with enterprise resource planning systems to perform read-only purchase order verification and authorized ledger postings.

```mermaid
flowchart TD
    A[Action Agent: erp.post_invoice] --> B[ERP Connector Gateway]
    
    B --> C{ERP System Type}
    
    C -->|SAP S/4HANA Cloud| D[SAP OData / REST API v4]
    C -->|Oracle NetSuite / Cloud| E[SuiteTalk REST Web Services]
    C -->|Internal ERP / Custom| F[Custom Enterprise REST Endpoint]
    
    D & E & F --> G[Attach Idempotency Key & TLS Client Cert]
    G --> H[Execute Journal Entry Transaction]
    H --> I[Capture External Document Number & Return Receipt]
```

---

## 2. Supported ERP Operations

* **`erp.get_purchase_order`**: Fetches PO line items, authorized totals, vendor identifiers, and delivery receipts.
* **`erp.post_invoice`**: Submits a reconciled invoice for general ledger posting with debit/credit account distribution.
* **`erp.check_inventory`**: Queries live stock levels and warehouse bin locations.
