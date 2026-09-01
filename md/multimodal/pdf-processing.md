# Multimodal — High-Fidelity PDF Processing & Layout Analysis

## Status
**Status:** ✅ IMPLEMENTED (PyMuPDF + pdfplumber Hybrid Pipeline)

---

## 1. PDF Ingestion Architecture

PDFs represent the predominant format for enterprise knowledge, financial statements, and technical manuals. OmniAgent AI deploys a **dual-mode PDF extraction engine** that automatically determines whether a document is a digital vector PDF or a scanned bitmap, applying the optimal extraction strategy.

```mermaid
flowchart TD
    A[Incoming PDF Document] --> B[PyMuPDF Header & Font Introspector]
    
    B --> C{Character Density >= 50 chars/page?}
    
    C -->|Yes: Digital Vector PDF| D[PyMuPDF + pdfplumber Structured Text & Table Extractor]
    C -->|No: Scanned Bitmap PDF| E[PDF-to-Image Rasterizer: 300 DPI Rendering]
    
    E --> F[Hybrid OCR Engine: Tesseract + Vision LLM]
    
    D --> G[Layout Geometry & Table Grid Reconstruction]
    F --> G
    
    G --> H[Semantic Markdown Formatter with Page Metadata]
    H --> I[Vector Indexing & RAG Store]
```

---

## 2. Table & Layout Reconstruction

* **Table Extraction:** Uses `pdfplumber` line-intersection detection algorithms to convert complex multi-column financial balance sheets into structured Markdown tables.
* **Header Hierarchy Detection:** Inspects font sizes and weights in PyMuPDF spans to reconstruct Markdown `#`, `##`, `###` heading outlines.
* **Bounding Box Tracking:** Associates every extracted text block with its page coordinate rectangle `(x0, y0, x1, y1)` for instant visual highlighting in the Next.js PDF viewer.
