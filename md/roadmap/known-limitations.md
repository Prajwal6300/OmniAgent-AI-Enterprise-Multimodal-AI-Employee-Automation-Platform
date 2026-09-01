# Roadmap — Known Operational Limitations & Engineering Mitigations

## Status
**Status:** ⚠️ KNOWN LIMITATIONS & MITIGATIONS

---

## 1. Document Complexity & File Size Caps
* **Limitation:** Single documents exceeding 500 pages or 100MB can experience extraction timeouts if processed in a single synchronous Celery task.
* **Mitigation:** Ingestion workers automatically split large PDFs into 50-page partitions, parallelizing OCR across Celery worker pools.

---

## 2. Low-Resolution Cursive Handwriting OCR
* **Limitation:** Degraded, low-DPI cursive handwriting from legacy field forms exhibits higher error rates with standard Tesseract OCR.
* **Mitigation:** The system flags confidence scores $<0.75$ and routes the region of interest to Tier 2 Vision LLMs (GPT-4o / Claude 3.5 Sonnet) or requests operator manual review.

---

## 3. Real-Time High-Frame-Rate Video Analytics
* **Limitation:** Live 60 FPS video streams cannot be parsed frame-by-frame due to prohibitive token costs and compute latency.
* **Mitigation:** The video ingestion engine samples keyframes on scene change thresholds or 5-second intervals rather than continuous streaming.
