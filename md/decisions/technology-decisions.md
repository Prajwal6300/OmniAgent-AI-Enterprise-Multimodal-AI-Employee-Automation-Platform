# Architecture Decision Records — ADR 002: Core Technology Stack Selection

## Status
**Status:** ✅ ACCEPTED & IMPLEMENTED

---

## 1. Why FastAPI for Backend?
* **Context:** High-throughput async I/O required for concurrent SSE streams, database pools, and third-party LLM calls.
* **Decision:** Adopt **FastAPI (Python 3.11+)** with Pydantic v2.
* **Rationale:** First-class async/await support, automatic OpenAPI/Swagger documentation, strict type validation, and seamless integration with Python ML/AI libraries.

---

## 2. Why PostgreSQL 16 + pgvector?
* **Context:** Need for relational ACID metadata storage and high-dimensional semantic vector search.
* **Decision:** Adopt **PostgreSQL 16 with `pgvector` extension (HNSW indexing)**.
* **Rationale:** Consolidates relational data, JSONB state, and vector embeddings into a single enterprise database engine, eliminating the operational overhead and synchronization lag of separate dedicated vector databases (e.g., Pinecone/Milvus).

---

## 3. Why Next.js 14 (App Router) + Tailwind CSS + Shadcn UI?
* **Context:** Modern, accessible, high-performance web dashboard with streaming response rendering and document sidecars.
* **Decision:** Adopt **Next.js 14 App Router, React 18, Tailwind CSS, and Shadcn UI**.
* **Rationale:** Server-side rendering, optimized client bundling, accessibility (WCAG AA), and modular composable UI primitives.
