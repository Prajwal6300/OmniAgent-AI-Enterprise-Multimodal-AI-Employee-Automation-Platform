# Development — Git Workflow, Branching Strategy & Releases

## Status
**Status:** ✅ IMPLEMENTED (GitHub Flow & Conventional Commits)

---

## 1. Branching Strategy

OmniAgent AI follows the **GitHub Flow** with protected `main` and `develop` branches:
* **`main`**: Production-ready code; tagged with semantic releases (`v1.0.0`).
* **`develop`**: Active integration branch for staging verification.
* **`feature/<issue-id>-<short-description>`**: New features and agent capabilities.
* **`fix/<issue-id>-<short-description>`**: Bug fixes and security patches.

---

## 2. Conventional Commit Specifications

Commits must follow the **Conventional Commits 1.0.0** format:
* `feat(agents): implement dynamic tool auto-healing in supervisor`
* `fix(rag): correct cosine distance calculation in pgvector adapter`
* `docs(api): document approval endpoints and JSON schemas`
* `refactor(backend): migrate database sessions to asyncpg connection pool`
