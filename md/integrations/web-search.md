# Integrations — Web Search Connectors (Tavily & DuckDuckGo)

## Status
**Status:** ✅ IMPLEMENTED (Tavily Search API & DuckDuckGo Fallback)

---

## 1. Web Search Architecture

When an enterprise inquiry requires external real-time verification (e.g., checking if a vendor company is actively registered, checking currency foreign exchange rates, or reviewing market competitor prices), the RAG Agent or Supervisor invokes the **Web Search Connector**.

```mermaid
flowchart TD
    A[Agent Search Directive] --> B[Web Search Gateway Router]
    
    B --> C{Primary Provider Available?}
    C -->|Yes| D[Tavily Search API - AI Optimized Context]
    C -->|No / Rate Limited| E[DuckDuckGo HTML/API Fallback]
    
    D & E --> F[Extract Raw Web Snippets & Sources]
    F --> G[Relevance Filtering & Content Cleaning]
    G --> H[Return Grounded Web Context with URLs to Agent]
```

---

## 2. Configuration Parameters

```env
TAVILY_API_KEY=<YOUR_TAVILY_API_KEY>
WEB_SEARCH_MAX_RESULTS=5
WEB_SEARCH_INCLUDE_DOMAINS=["gov.uk", "sec.gov", "bloomberg.com", "reuters.com"]
```
