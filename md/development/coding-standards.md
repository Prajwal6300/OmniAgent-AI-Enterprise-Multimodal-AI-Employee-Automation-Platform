# Development — Coding Standards, Linting & Type Safety

## Status
**Status:** ✅ IMPLEMENTED (Black, Ruff, Mypy, ESLint & Prettier)

---

## 1. Backend Python Standards (PEP 8 + Strict Typing)

* **Code Formatter:** `black --line-length 100`
* **Linter & Import Sorter:** `ruff check . --fix`
* **Static Type Checker:** `mypy app --strict`
* **Pydantic Validation:** All incoming and outgoing data structures must be typed with Pydantic v2 `BaseModel` classes. No raw untyped `dict` returns from services.

---

## 2. Frontend TypeScript Standards

* **Linter:** `eslint` with Next.js & TypeScript rules.
* **Formatter:** `prettier` with Tailwind CSS plugin.
* **Strict TypeScript:** `noImplicitAny: true`, `strictNullChecks: true`.
* **Component Architecture:** Small, composable React Server Components (RSC) where possible; `'use client'` only on stateful/interactive leaves.
