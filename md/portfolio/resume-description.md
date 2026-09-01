# Portfolio — Professional Resume Description & High-Impact Bullets

---

## 1. Short Resume Description (2–3 Lines)

> **OmniAgent AI — Enterprise Multimodal AI Employee & Automation Platform**
> Engineered a production-grade autonomous multimodal AI employee and workflow automation platform using LangGraph, FastAPI, PostgreSQL (pgvector), and Next.js 14. Ingests PDFs, images, audio, and relational data to execute enterprise reconciliations with risk-tiered human approval gating and tamper-proof HMAC audit trails.

---

## 2. High-Impact Resume Bullet Points

* **Architected Stateful Multi-Agent Swarm:** Designed and deployed a hierarchical LangGraph multi-agent architecture (Supervisor, Vision, Document, RAG, Database, Reasoning, Action agents) coordinating complex cross-modal enterprise workflows with sub-second task routing.
* **Engineered Hybrid Enterprise RAG:** Implemented a sub-50ms hybrid vector retrieval pipeline in PostgreSQL 16 using `pgvector` HNSW indexing, BM25 full-text search, and Cross-Encoder reranking, achieving 97.2% groundedness on Ragas benchmarks with zero hallucinations.
* **Built Multimodal Ingestion Pipeline:** Developed high-throughput asynchronous extraction services utilizing PyMuPDF, pdfplumber, OpenCV, Tesseract OCR, and Faster-Whisper ASR, processing 100-page complex PDF contracts and audio memos in under 6 seconds.
* **Implemented Deterministic HITL & Risk Gating:** Built a 3-tier risk classification engine (LOW, MEDIUM, HIGH) that suspends high-stakes database mutations and ERP transactions until cryptographically authorized by human operators via a Next.js 14 approval portal.
* **Constructed Zero-Trust Enterprise Security:** Hardened the platform with strict prompt delimiter sandboxing (`<<<UNTRUSTED_CONTENT>>>`), AST-validated read-only SQL sandboxes, multi-tenant row-level security (RLS), and HMAC SHA-256 tamper-evident audit ledgers.
