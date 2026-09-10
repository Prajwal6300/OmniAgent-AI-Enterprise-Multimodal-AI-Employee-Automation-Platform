import re
from typing import Any

from agents.document.schemas import (
    DocumentPage,
    DocumentType,
    InvoiceData,
    PolicyData,
    ReportData,
    TechnicalManualData,
)


def heuristic_classify_document(text: str, filename: str = "") -> tuple[DocumentType, float, str]:
    """
    High-performance pattern classifier for enterprise documents.
    Returns (document_type, confidence, inferred_title).
    """
    text_lower = text.lower()
    fn_lower = filename.lower()

    # 1. INVOICE / BILLING
    invoice_keywords = [
        "invoice", "tax invoice", "bill to", "subtotal", "total amount",
        "balance due", "amount payable", "invoice number", "inv-", "gstin", "vat"
    ]
    invoice_score = sum(1 for kw in invoice_keywords if kw in text_lower or kw in fn_lower)
    if "invoice" in fn_lower or invoice_score >= 3:
        title = _extract_first_matching_line(text, ["invoice", "tax invoice", "bill"]) or "Invoice"
        return DocumentType.INVOICE, 0.96, title

    # 2. POLICY / HANDBOOK
    policy_keywords = [
        "leave policy", "hr policy", "policy statement", "eligibility",
        "employee handbook", "maternity leave", "sick leave", "code of conduct",
        "compliance policy", "guidelines and procedures"
    ]
    policy_score = sum(1 for kw in policy_keywords if kw in text_lower or kw in fn_lower)
    if "policy" in fn_lower or policy_score >= 2:
        title = _extract_first_matching_line(text, ["policy", "guidelines", "handbook"]) or "Company Policy"
        return DocumentType.POLICY, 0.95, title

    # 3. TECHNICAL MANUAL
    manual_keywords = [
        "user manual", "operating instructions", "safety instructions", "technical manual",
        "caution", "warning", "maintenance", "troubleshooting", "specifications", "installation guide",
        "instruction", "operating", "machine manual"
    ]
    manual_score = sum(1 for kw in manual_keywords if kw in text_lower or kw in fn_lower)
    if "manual" in fn_lower or manual_score >= 2:
        title = _extract_first_matching_line(text, ["manual", "instructions", "guide", "operating"]) or "Technical Manual"
        return DocumentType.TECHNICAL_MANUAL, 0.94, title

    # 4. REPORT
    report_keywords = [
        "executive summary", "annual report", "quarterly report", "findings",
        "market research", "financial analysis", "key findings", "conclusion"
    ]
    report_score = sum(1 for kw in report_keywords if kw in text_lower or kw in fn_lower)
    if "report" in fn_lower or report_score >= 2:
        title = _extract_first_matching_line(text, ["report", "quarterly", "summary"]) or "Executive Report"
        return DocumentType.REPORT, 0.93, title

    # 5. CONTRACT
    contract_keywords = ["agreement", "terms and conditions", "parties agree", "non-disclosure", "nda", "contract"]
    if any(kw in fn_lower for kw in ["contract", "agreement", "nda"]) or sum(1 for kw in contract_keywords if kw in text_lower) >= 2:
        return DocumentType.CONTRACT, 0.92, "Contract Agreement"

    # 6. RESUME
    resume_keywords = ["curriculum vitae", "work experience", "skills & abilities", "education", "employment history"]
    if "resume" in fn_lower or "cv" in fn_lower or sum(1 for kw in resume_keywords if kw in text_lower) >= 3:
        return DocumentType.RESUME, 0.92, "Professional Resume"

    # 7. PURCHASE ORDER
    if "purchase order" in text_lower or "purchase order" in fn_lower or "po #" in text_lower:
        return DocumentType.PURCHASE_ORDER, 0.94, "Purchase Order"

    # Default fallback
    if len(text.strip()) > 30:
        first_line = text.strip().split("\n")[0][:60]
        return DocumentType.GENERAL_DOCUMENT, 0.75, first_line or "General Document"

    return DocumentType.UNKNOWN, 0.0, "Unknown Document"


def _extract_first_matching_line(text: str, keywords: list[str]) -> str | None:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines[:10]:
        if any(kw in line.lower() for kw in keywords) and len(line) < 80:
            return line
    return None


def extract_deterministic_invoice(text: str, pages: list[DocumentPage]) -> tuple[InvoiceData, list[dict[str, Any]]]:
    """
    Extracts invoice fields with source page citations without hallucinating.
    """
    sources: list[dict[str, Any]] = []

    # Helper to find source page
    def find_page_for_regex(pattern: str) -> int | None:
        for p in pages:
            if re.search(pattern, p.text, re.IGNORECASE):
                return p.page_number
        return 1 if pages else None

    # Vendor extraction
    vendor = None
    vendor_match = re.search(r"(?:vendor|supplier|from|billed by|company):\s*([^\n\r,\u25a0]+)", text, re.IGNORECASE)
    if vendor_match:
        vendor = vendor_match.group(1).strip()
    else:
        # Check first non-empty lines
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:3]:
            if not any(k in line.lower() for k in ["invoice", "tax", "bill", "date"]):
                vendor = line
                break
    if vendor:
        p_num = find_page_for_regex(re.escape(vendor[:20]))
        sources.append({"field": "vendor", "value": vendor, "source": {"page": p_num}})

    # Invoice Number
    inv_num = None
    inv_match = re.search(r"invoice\s*(?:number|no|#)?\s*[:#]\s*([A-Za-z0-9\-_]+)", text, re.IGNORECASE)
    if not inv_match:
        inv_match = re.search(r"\b(INV-[A-Za-z0-9\-_]+)\b", text, re.IGNORECASE)
    if inv_match:
        inv_num = inv_match.group(1).strip()
        p_num = find_page_for_regex(re.escape(inv_num))
        sources.append({"field": "invoice_number", "value": inv_num, "source": {"page": p_num}})

    # Date
    date_val = None
    date_match = re.search(r"(?:date|invoice date)[:\s]+([0-9]{1,4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,4}|[A-Za-z]+ \d{1,2},? \d{4})", text, re.IGNORECASE)
    if date_match:
        date_val = date_match.group(1).strip()
        p_num = find_page_for_regex(re.escape(date_val))
        sources.append({"field": "date", "value": date_val, "source": {"page": p_num}})

    # Subtotal
    subtotal = None
    subtotal_match = re.search(r"\b(?:subtotal|sub-total|sub total)[:\s]+([₹$€£]?\s*[\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
    if subtotal_match:
        subtotal = subtotal_match.group(1).strip()
        p_num = find_page_for_regex(r"subtotal")
        sources.append({"field": "subtotal", "value": subtotal, "source": {"page": p_num}})

    # Tax
    tax = None
    tax_match = re.search(r"\b(?:tax|vat|gst)[:\s]+([₹$€£]?\s*[\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
    if tax_match:
        tax = tax_match.group(1).strip()
        p_num = find_page_for_regex(r"(?:tax|vat|gst)")
        sources.append({"field": "tax", "value": tax, "source": {"page": p_num}})

    # Total
    total = None
    total_match = re.search(r"\b(?:grand total|total amount|amount due|balance due|total)[:\s]+([₹$€£]?\s*[\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
    if total_match:
        total = total_match.group(1).strip()
        p_num = find_page_for_regex(r"(?:total|grand total)")
        sources.append({"field": "total", "value": total, "source": {"page": p_num}})

    # Currency
    currency = "USD"
    if "₹" in text or "inr" in text.lower():
        currency = "INR"
    elif "€" in text or "eur" in text.lower():
        currency = "EUR"
    elif "£" in text or "gbp" in text.lower():
        currency = "GBP"
    elif "$" in text or "usd" in text.lower():
        currency = "USD"

    # Line Items
    line_items: list[dict[str, Any]] = []
    item_matches = re.findall(r"([A-Za-z0-9\s\-]+?)\s+(\d+)\s+([₹$€£]?[\d,]+(?:\.\d{2})?)\s+([₹$€£]?[\d,]+(?:\.\d{2})?)", text)
    for im in item_matches:
        desc, qty, unit_p, line_tot = im
        desc = desc.strip()
        if desc.lower() not in ["description", "item", "subtotal", "total", "tax"]:
            line_items.append({
                "description": desc,
                "quantity": qty,
                "unit_price": unit_p,
                "total": line_tot
            })

    invoice_data = InvoiceData(
        vendor=vendor or "Not found in the provided document.",
        invoice_number=inv_num or "Not found in the provided document.",
        date=date_val or "Not found in the provided document.",
        subtotal=subtotal or "Not found in the provided document.",
        tax=tax or "Not found in the provided document.",
        total=total or "Not found in the provided document.",
        currency=currency,
        line_items=line_items
    )
    return invoice_data, sources


def extract_deterministic_policy(text: str, pages: list[DocumentPage]) -> tuple[PolicyData, list[dict[str, Any]]]:
    """
    Extracts policy elements: summary, important rules, eligibility, restrictions, relevant sections.
    """
    sources: list[dict[str, Any]] = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    rules: list[str] = []
    eligibility: list[str] = []
    restrictions: list[str] = []
    sections: list[str] = []

    for line in lines:
        l_lower = line.lower()
        if any(h in l_lower for h in ["section", "policy:", "article"]):
            sections.append(line)
        elif any(e in l_lower for e in ["eligible", "eligibility", "applies to", "all employees"]):
            eligibility.append(line)
            sources.append({"field": "eligibility", "value": line, "source": {"page": 1}})
        elif any(r in l_lower for r in ["must not", "prohibited", "restriction", "maximum", "not permitted", "limit"]):
            restrictions.append(line)
            sources.append({"field": "restrictions", "value": line, "source": {"page": 1}})
        elif any(rule in l_lower for rule in ["must", "required", "shall", "entitled", "days of leave"]):
            rules.append(line)
            sources.append({"field": "important_rules", "value": line, "source": {"page": 1}})

    summary = (
        f"This policy outlines organizational regulations governing {sections[0] if sections else 'company conduct and leave entitlements'}."
        if sections or rules
        else "Company operational policy document."
    )

    policy_data = PolicyData(
        summary=summary,
        important_rules=rules[:10] if rules else ["All employees must adhere to the stipulated guidelines."],
        eligibility=eligibility[:5] if eligibility else ["Not found in the provided document."],
        restrictions=restrictions[:5] if restrictions else ["Standard operational restrictions apply."],
        relevant_sections=sections[:10] if sections else ["General Policy"]
    )
    return policy_data, sources


def extract_deterministic_technical_manual(text: str, pages: list[DocumentPage]) -> tuple[TechnicalManualData, list[dict[str, Any]]]:
    """
    Extracts technical manual data: summary, key instructions, warnings, relevant sections.
    """
    sources: list[dict[str, Any]] = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    instructions: list[str] = []
    warnings: list[str] = []
    sections: list[str] = []

    for line in lines:
        l_lower = line.lower()
        if any(w in l_lower for w in ["warning", "caution", "danger", "hazard", "risk"]):
            warnings.append(line)
            sources.append({"field": "warnings", "value": line, "source": {"page": 1}})
        elif any(step in l_lower for step in ["step", "press", "connect", "ensure", "turn on", "install", "power"]):
            instructions.append(line)
            sources.append({"field": "key_instructions", "value": line, "source": {"page": 1}})
        elif any(s in l_lower for s in ["section", "chapter", "specifications", "maintenance"]):
            sections.append(line)

    summary = "Technical operating instructions and safety procedures for equipment operation."
    manual_data = TechnicalManualData(
        summary=summary,
        key_instructions=instructions[:10] if instructions else ["Not found in the provided document."],
        warnings=warnings[:10] if warnings else ["Not found in the provided document."],
        relevant_sections=sections[:10] if sections else ["Operating Instructions"]
    )
    return manual_data, sources


def extract_deterministic_report(text: str, pages: list[DocumentPage]) -> tuple[ReportData, list[dict[str, Any]]]:
    """
    Extracts report data: executive summary, important findings, numbers, conclusions, warnings.
    """
    sources: list[dict[str, Any]] = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    findings: list[str] = []
    numbers: list[str] = []
    conclusions: list[str] = []
    warnings: list[str] = []

    for line in lines:
        l_lower = line.lower()
        # Find numbers
        num_matches = re.findall(r"([₹$€£]?\s*[\d,]+(?:\.\d+)?%?)", line)
        for nm in num_matches:
            if len(nm.strip()) > 1 and nm.strip() not in numbers:
                numbers.append(nm.strip())

        if any(f in l_lower for f in ["finding", "result", "demonstrates", "showed", "increased", "decreased"]):
            findings.append(line)
            sources.append({"field": "important_findings", "value": line, "source": {"page": 1}})
        elif any(c in l_lower for c in ["conclusion", "recommend", "next steps", "finally"]):
            conclusions.append(line)
            sources.append({"field": "conclusions", "value": line, "source": {"page": 1}})
        elif any(w in l_lower for w in ["warning", "risk", "limitation", "deficit", "decline"]):
            warnings.append(line)
            sources.append({"field": "warnings", "value": line, "source": {"page": 1}})

    exec_summary = lines[0] if lines else "Executive report summary."
    report_data = ReportData(
        executive_summary=exec_summary,
        important_findings=findings[:10] if findings else ["Not found in the provided document."],
        numbers=numbers[:15] if numbers else ["Not found in the provided document."],
        conclusions=conclusions[:5] if conclusions else ["Not found in the provided document."],
        warnings=warnings[:5] if warnings else ["No critical risks identified in report."]
    )
    return report_data, sources
