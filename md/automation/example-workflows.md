# Automation — Production Example Workflow Definitions

## Status
**Status:** ✅ IMPLEMENTED (Verified Production JSON/YAML DAGs)

---

## 1. Production Invoice 3-Way Match & ERP Post DAG

```json
{
  "workflow_id": "wf_invoice_3way_match",
  "name": "Accounts Payable 3-Way Matching & Posting",
  "version": "1.2.0",
  "description": "Extracts vendor invoices, reconciles against ERP PO and goods receipt, gates high amounts for manager approval, and posts to SAP.",
  "trigger": {
    "type": "file_upload",
    "bucket": "omni-enterprise-artifacts",
    "prefix": "invoices/incoming/"
  },
  "nodes": [
    {
      "id": "node_extract_pdf",
      "type": "agent",
      "agent": "document_agent",
      "params": {
        "schema": "CommercialInvoiceSchema",
        "enable_ocr_fallback": true
      }
    },
    {
      "id": "node_fetch_po",
      "type": "agent",
      "agent": "database_agent",
      "params": {
        "query_template": "SELECT * FROM purchase_orders WHERE po_number = :po_number AND tenant_id = :tenant_id"
      }
    },
    {
      "id": "node_match_reconcile",
      "type": "agent",
      "agent": "reasoning_agent",
      "params": {
        "matching_rules": ["price_variance_max_1_pct", "quantity_exact_match"],
        "tax_verification": true
      }
    },
    {
      "id": "node_approval_gate",
      "type": "human_approval",
      "condition": "steps.node_extract_pdf.total_amount > 5000.00 || steps.node_match_reconcile.variance_pct > 0.00",
      "risk_level": "HIGH",
      "required_roles": ["finance_manager", "admin"]
    },
    {
      "id": "node_erp_post",
      "type": "action",
      "action": "erp.post_invoice",
      "params": {
        "invoice_data": "$steps.node_extract_pdf.output",
        "po_reference": "$steps.node_fetch_po.output.po_number"
      }
    },
    {
      "id": "node_slack_notify",
      "type": "action",
      "action": "slack.post_card",
      "params": {
        "channel": "#finance-ops",
        "message": "Invoice $steps.node_extract_pdf.invoice_id posted successfully to ERP."
      }
    }
  ],
  "edges": [
    { "from": "node_extract_pdf", "to": "node_fetch_po" },
    { "from": "node_fetch_po", "to": "node_match_reconcile" },
    { "from": "node_match_reconcile", "to": "node_approval_gate" },
    { "from": "node_approval_gate", "to": "node_erp_post" },
    { "from": "node_erp_post", "to": "node_slack_notify" }
  ]
}
```

---

## 2. IT Support Screenshot Diagnosis & Jira Ticket DAG

```json
{
  "workflow_id": "wf_it_screenshot_triage",
  "name": "IT Error Screenshot Triage & Incident Creation",
  "version": "1.0.0",
  "trigger": {
    "type": "manual_api",
    "endpoint": "/api/v1/workflows/it-triage/trigger"
  },
  "nodes": [
    {
      "id": "node_vision_ocr",
      "type": "agent",
      "agent": "vision_agent",
      "params": { "task": "extract_error_stacktrace" }
    },
    {
      "id": "node_rag_runbook",
      "type": "agent",
      "agent": "rag_agent",
      "params": { "category": "devops_runbooks", "top_k": 3 }
    },
    {
      "id": "node_synthesize_remediation",
      "type": "agent",
      "agent": "reasoning_agent"
    },
    {
      "id": "node_jira_create",
      "type": "action",
      "action": "jira.create_issue",
      "params": {
        "project_key": "DEVOPS",
        "issue_type": "Bug",
        "summary": "Automated Crash Triage: $steps.node_vision_ocr.error_name",
        "description": "$steps.node_synthesize_remediation.remediation_markdown"
      }
    }
  ],
  "edges": [
    { "from": "node_vision_ocr", "to": "node_rag_runbook" },
    { "from": "node_rag_runbook", "to": "node_synthesize_remediation" },
    { "from": "node_synthesize_remediation", "to": "node_jira_create" }
  ]
}
```
