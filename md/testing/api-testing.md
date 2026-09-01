# Testing — End-to-End API Testing & Postman Collection

## Status
**Status:** ✅ IMPLEMENTED

---

## 1. Automated API E2E Suite

The API test suite (`tests/e2e/test_api_flows.py`) validates complete business journeys:
1. User registration -> Login -> JWT acquisition.
2. Direct document upload -> Async ingestion trigger -> Verification of vector indexing.
3. Conversational chat stream initiation -> Checking SSE event structure.
4. Human approval creation -> Operator approval decision -> Verifying workflow resumption.

---

## 2. Postman / Newman CLI Automation

```bash
# Execute full API regression suite via Newman CLI
newman run postman/OmniAgent_API_Collection.json \
  -e postman/OmniAgent_Dev_Environment.json \
  --reporters cli,junit --reporter-junit-export reports/newman-results.xml
```
