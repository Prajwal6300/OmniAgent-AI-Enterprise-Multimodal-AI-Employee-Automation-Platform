# Security — Data Privacy, PII Redaction & Compliance (GDPR / HIPAA)

## Status
**Status:** 🚧 PARTIALLY IMPLEMENTED (Regex & NER PII Redaction Active; Dynamic Masking in Progress)

---

## 1. Data Privacy Framework

OmniAgent AI is architected to adhere to international data protection regulations (GDPR, CCPA, HIPAA) by guaranteeing that sensitive Personally Identifiable Information (PII) is masked before transmission to external LLM providers or indexing into vector databases.

```mermaid
flowchart TD
    A[Raw Document Text / Ingestion Stream] --> B[PII & Sensitive Pattern Detector]
    
    B --> C{Detect Sensitive Entities}
    C -->|SSN / Tax ID| D[Redact: [REDACTED_SSN]]
    C -->|Credit Card Number| E[Redact: [REDACTED_CARD]]
    C -->|Phone / Personal Email| F[Redact: [REDACTED_CONTACT]]
    C -->|Medical / PHI Terms| G[Redact: [REDACTED_PHI]]
    
    D & E & F & G --> H[Sanitized Document Text]
    H --> I[Vector Embedding & External LLM Processing]
```

---

## 2. Privacy Guarantees

* **Zero LLM Training:** Commercial API agreements with OpenAI, Anthropic, and Google strictly enforce zero retention and zero training on enterprise data.
* **On-Premises Air-Gapped Mode:** Organizations with strict data residency mandates can run fully offline using local Ollama LLMs and PostgreSQL pgvector.
* **Right to be Forgotten (GDPR Art. 17):** Deleting a user or document cascades soft-deletes and triggers vector embedding purge from `document_chunks`.
