# Testing — Unit Testing Suites (Pytest & Vitest)

## Status
**Status:** ✅ IMPLEMENTED

---

## 1. Backend Unit Tests (`tests/unit/`)

* **Pydantic Schemas:** Tests field validation, regex pattern matching (PO numbers, Tax IDs), and default values.
* **Text & PDF Chunker:** Tests that split chunks respect sentence boundaries and preserve Markdown table formats.
* **HMAC Signatures:** Verifies that modifying a single byte in an audit payload causes signature re-computation failure.

---

## 2. Frontend Unit Tests (`frontend/tests/`)

* **UI Store Tests:** Verifies active session switching, sidebar collapse, and dark mode toggles.
* **Component Rendering:** Tests that `ApprovalCard` correctly renders risk badge styles (`HIGH` = red) and disables actions when user lacks required role.
