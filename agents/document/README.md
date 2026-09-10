# Document Agent (OmniAgent AI)

## Overview

The **Document Agent** is an enterprise-grade document intelligence specialist designed to validate, extract, classify, and analyze multi-page business documents (PDF, DOCX, TXT). It integrates into the OmniAgent AI cognitive mesh via LangGraph and works under the orchestration of the Supervisor Agent.

## Core Capabilities

- **Strict File Validation**: Enforces MIME types, file extensions, size limits (up to 25MB), empty file rejection, and path traversal protection.
- **High-Fidelity Text Extraction**:
  - **PDF**: Page-by-page extraction via `pypdf` with 1-indexed page numbering and OCR detection for scanned documents.
  - **DOCX**: Extracts structured paragraphs, headings, and tables via `python-docx`.
  - **TXT**: Multi-encoding normalization (UTF-8, Latin-1, CP1252) with line break cleaning.
- **Enterprise Classification**:
  - `INVOICE`: Billing, tax breakdown, vendor, date, line items.
  - `POLICY`: Leave rules, eligibility, restrictions, relevant sections.
  - `TECHNICAL_MANUAL`: Operating steps, safety cautions, equipment specs.
  - `REPORT`: Executive summaries, findings, key metrics, conclusions.
  - `CONTRACT`, `RESUME`, `PURCHASE_ORDER`, `GENERAL_DOCUMENT`.
- **Anti-Hallucination & Provenance**:
  - Strictly returns `"Not found in the provided document"` when information is absent.
  - Attaches source citations (`page`, `section`, `paragraph`) to all extracted entities.
- **Security Guardrails**:
  - Multi-tenant tenant access enforcement.
  - Untrusted content delimiter and prompt injection defenses against override attempts.
  - No live external tool execution.

## LangGraph Workflow

```text
START
  ↓
validate_document
  ↓
extract_text
  ↓
normalize_content
  ↓
classify_document
  ↓
understand_document
  ↓
validate_result
  ↓
END
```

## Quick Usage

```python
from agents.document import DocumentAgent

agent = DocumentAgent()

result = await agent.analyze(
    document_id="doc-12345",
    file_bytes=pdf_bytes,
    filename="Invoice_001.pdf",
    task="extract_information"
)

print(result.document_type)  # "INVOICE"
print(result.summary)
print(result.structured_data)
```
