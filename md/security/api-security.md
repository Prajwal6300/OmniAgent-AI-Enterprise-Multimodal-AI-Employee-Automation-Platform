# Security — API Security, Rate Limiting & Input Validation

## Status
**Status:** ✅ IMPLEMENTED (Pydantic v2, Redis Rate Limiting, CORS & HTTPS)

---

## 1. API Security Architecture

OmniAgent AI secures its public and internal API surfaces against automated scraping, credential stuffing, and injection attacks.

```mermaid
flowchart TD
    A[Incoming HTTP Request] --> B[TLS 1.3 Termination & HTTPS Redirect]
    B --> C[CORS Origin Whitelist Check]
    
    C --> D[Redis Token Bucket Rate Limiter: 120 req/min]
    D -->|Exceeded| E[Return 429 Too Many Requests]
    
    D -->|Passed| F[Security Headers Injection: HSTS, CSP, X-Frame-Options]
    F --> G[Pydantic v2 Schema & Payload Size Validator]
    
    G -->|Invalid| H[Return 422 Unprocessable Entity]
    G -->|Valid| I[Forward to FastAPI Route Controller]
```

---

## 2. Security Headers Configuration

FastAPI injects strict enterprise security headers on every response:
* `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
* `X-Content-Type-Options: nosniff`
* `X-Frame-Options: DENY`
* `Content-Security-Policy: default-src 'self'; script-src 'self';`
* `Referrer-Policy: strict-origin-when-cross-origin`
