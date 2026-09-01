# Backend — Authentication & Session Management

## Status
**Status:** ✅ IMPLEMENTED (OAuth2 Password Flow + JWT Bearer Tokens)

---

## 1. Authentication Architecture

Authentication in OmniAgent AI utilizes industry-standard **OAuth2 with Password Bearer flow** and cryptographic JSON Web Tokens (JWT).

```mermaid
flowchart TD
    A[User Enters Email & Password] --> B[POST /api/v1/auth/login]
    B --> C[Fetch User by Email from DB]
    
    C --> D{Verify Password via Passlib / Bcrypt}
    
    D -->|Invalid Password| E[Increment Failed Login Count & Throw 401]
    D -->|Valid Password| F[Generate Access Token + Refresh Token]
    
    F --> G[Store Refresh Token in DB / Redis]
    G --> H[Return JWT Access Token - 15m Exp + Refresh Token - 7d Exp]
    
    H --> I[Client Attaches 'Authorization: Bearer <JWT>' to Requests]
    I --> J[FastAPI Auth Middleware Validates Signature & Expiration]
```

---

## 2. Token Security Specifications

* **Access Token:** Short-lived (15 minutes), signed using HMAC SHA-256 (`HS256`) containing `user_id`, `email`, `role`, `tenant_id`, and `exp`.
* **Refresh Token:** Long-lived (7 days), stored in encrypted database table; rotated upon every refresh invocation.
* **Password Hashing:** Passlib with `bcrypt` (12 work factor rounds).
* **Brute-Force Protection:** IP & email rate-limited to 5 failed attempts per 15-minute window via Redis token bucket.
