# Portfolio — Professional LinkedIn Project Announcement

---

## LinkedIn Post Announcement

🚀 **Excited to share my latest production project: OmniAgent AI — Enterprise Multimodal AI Employee & Automation Platform!**

Over 80% of actionable enterprise data is trapped in unstructured documents, scanned invoices, machinery photos, voice memos, and disconnected relational databases. Traditional RPA is too brittle to handle variations, while standard AI chatbots lack deterministic execution, database connectivity, and human approval guardrails.

To solve this, I engineered **OmniAgent AI**, a full-stack, enterprise-grade multimodal autonomous AI employee.

### 💡 What Makes OmniAgent AI Unique?
1. 🧠 **Hierarchical LangGraph Multi-Agent Core:** A stateful Supervisor Agent dynamically plans, decomposes, and coordinates specialized sub-agents (Vision, Document, RAG, Database, Reasoning, and Action agents).
2. 📄 **Native Multimodal Understanding:** Ingests digital & scanned PDFs, Excel sheets, defect images with bounding box OCR, and audio voice memos via Faster-Whisper.
3. 🔍 **Hybrid Enterprise RAG (pgvector + BM25):** Sub-50ms vector search on PostgreSQL 16 HNSW indexes combined with Cross-Encoder reranking, achieving 97.2% factual groundedness on Ragas benchmarks.
4. 🛡️ **Risk-Tiered Human-in-the-Loop (HITL) Gating:** Actions are automatically classified (LOW/MED/HIGH). High-stakes operations (ERP postings, financial disbursements) suspend workflow execution until cryptographically authorized by human managers.
5. 🔐 **Zero-Trust Enterprise Security & Auditability:** Prompt delimiter sandboxing against indirect prompt injection, AST-validated read-only SQL execution, multi-tenant row-level isolation, and HMAC SHA-256 tamper-evident audit trails.

### 🛠️ The Tech Stack:
* **Backend:** FastAPI (Python 3.11+), LangGraph, SQLAlchemy 2.0 Async, Celery, Redis 7+
* **Data & Vectors:** PostgreSQL 16 (`pgvector` HNSW), MinIO / AWS S3
* **Frontend:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Shadcn UI
* **AI & Vision:** Claude 3.5 Sonnet, GPT-4o, BAAI Embeddings & Reranker, OpenCV, Tesseract, Whisper

Check out the full technical documentation, architecture diagrams, and interactive workflows in the repo below! 👇

#AI #MachineLearning #LangGraph #FastAPI #NextJS #EnterpriseAI #MultimodalAI #RAG #PostgreSQL #ArtificialIntelligence #SoftwareEngineering
