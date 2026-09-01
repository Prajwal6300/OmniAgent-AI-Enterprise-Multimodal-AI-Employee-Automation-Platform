# API — Authentication Endpoints (`/api/v1/auth`)

## Status
**Status:** ✅ IMPLEMENTED

---

## 1. POST `/api/v1/auth/login`
Authenticates user credentials and returns short-lived access and refresh tokens.

* **Method:** `POST`
* **Auth Required:** `None`
* **Rate Limit:** 5 requests / minute

### Request Payload
```json
{
  "email": "finance.lead@acme.com",
  "password": "SecurePassword123!"
}
```

### Response Payload (`200 OK`)
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "ref_88192039102830192830...",
    "token_type": "bearer",
    "expires_in_seconds": 900,
    "user": {
      "id": "usr_99120481",
      "email": "finance.lead@acme.com",
      "full_name": "Sarah Jenkins",
      "role": "manager",
      "tenant_id": "ten_001928"
    }
  }
}
```

---

## 2. POST `/api/v1/auth/refresh`
Rotates and issues a fresh access token using a valid refresh token.

* **Method:** `POST`
* **Request:** `{ "refresh_token": "ref_88192039102830192830..." }`
* **Response:** `{ "success": true, "data": { "access_token": "..." } }`

---

## 3. GET `/api/v1/auth/me`
Fetches current authenticated profile and assigned enterprise scopes.

* **Method:** `GET`
* **Headers:** `Authorization: Bearer <JWT>`
* **Response (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "id": "usr_99120481",
    "email": "finance.lead@acme.com",
    "role": "manager",
    "permissions": ["documents:read", "workflows:execute", "approvals:write"]
  }
}
```
