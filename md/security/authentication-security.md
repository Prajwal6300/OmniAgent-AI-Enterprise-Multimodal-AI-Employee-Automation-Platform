# Security — Authentication Security, Tokens & Password Policies

## Status
**Status:** ✅ IMPLEMENTED (HMAC SHA-256 JWT, Bcrypt 12-Rounds, Token Revocation)

---

## 1. Password Hashing & Salt Security

* **Algorithm:** `bcrypt` via Passlib library.
* **Work Factor:** 12 rounds (default iteration count).
* **Salt:** Cryptographically secure pseudo-random 16-byte salt generated per password hash.
* **Password Policy:** Minimum 12 characters, requiring uppercase, lowercase, numeric, and special characters.

---

## 2. JWT Cryptographic Specifications

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "usr_99120481",
    "email": "finance.lead@acme.com",
    "tenant_id": "ten_001928",
    "role": "manager",
    "jti": "jwt_uuid_771829314",
    "iat": 1786800000,
    "exp": 1786800900
  }
}
```

* **Short-Lived Access Tokens:** 15-minute expiration (`exp`).
* **Refresh Token Rotation:** Refreshing an access token revokes the old refresh token and issues a new cryptographically bound pair.
* **Token Blacklisting (Logout):** Revoked tokens have their `jti` stored in Redis with TTL matching remaining expiration, immediately terminating session validity across all API endpoints.
