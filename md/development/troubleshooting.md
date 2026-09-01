# Development — Troubleshooting & Common Issues

## Status
**Status:** ✅ IMPLEMENTED (Diagnostic Guide & Solutions)

---

## 1. Top Development & Runtime Issues

### Issue 1: `pgvector` Extension Not Found on Database Init
* **Symptom:** `asyncpg.exceptions.UndefinedObjectError: type "vector" does not exist`
* **Root Cause:** Standard PostgreSQL container image used instead of `pgvector/pgvector:pg16`.
* **Fix:** Update `docker-compose.yml` to use image `pgvector/pgvector:pg16` and run:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```

### Issue 2: Celery Worker Fails to Connect to Redis
* **Symptom:** `kombu.exceptions.OperationalError: [Errno 111] Connection refused`
* **Root Cause:** Redis container not running or wrong `REDIS_URL` in `.env`.
* **Fix:** Run `docker compose up -d redis` and verify `redis-cli ping` returns `PONG`.

### Issue 3: OCR Engine Throws Missing Tesseract Binary
* **Symptom:** `pytesseract.pytesseract.TesseractNotFoundError: tesseract is not installed`
* **Fix (Windows):** Install Tesseract via `winget install UB-Mannheim.TesseractOCR` and add to system `PATH`.
* **Fix (Linux):** Run `sudo apt-get install tesseract-ocr libtesseract-dev`.

### Issue 4: LLM Rate Limit / 429 Errors During Testing
* **Symptom:** `openai.RateLimitError: 429 You exceeded your current quota`
* **Fix:** Enable local fallback in `.env` by setting `OLLAMA_BASE_URL=http://localhost:11434` or set Tier 2 routing to `Claude 3.5 Haiku`.
