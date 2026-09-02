class InvoiceWorkflow:
    STEPS = [
        "extract_invoice_pdf",
        "validate_po_match",
        "assess_risk_gate",
        "post_erp_entry",
        "notify_accounts_payable"
    ]
