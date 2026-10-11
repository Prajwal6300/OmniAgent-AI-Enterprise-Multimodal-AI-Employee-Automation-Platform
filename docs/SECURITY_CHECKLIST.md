# OmniAgent AI — Security Checklist (Phase 1 Audit Final Status)

## Item 1: SQL Injection
- **Verdict**: OK
- **Evidence**: All DB queries use SQLAlchemy ORM parameterized queries. No raw f-strings/.format() building SQL. `text()` used only in health checks without user input.
- **Severity**: Low
- **Fix needed**: —

## Item 2: XSS
- **Verdict**: PARTIAL
- **Evidence**: Chat answers streamed as tokens could contain unsanitized HTML from agent responses. No CSP header configured in FastAPI.
- **Severity**: Medium
- **Fix needed**: Add CSP header, sanitize agent outputs

## Item 3: CSRF
- **Verdict**: OK
- **Evidence**: JWT auth uses Authorization header with Bearer token. No cookies used for auth. Token in localStorage but sent via header, not cookie-based CSRF vector.
- **Severity**: Low
- **Fix needed**: —

## Item 4: File Uploads
- **Verdict**: PARTIAL
- **Evidence**: Extension check for .pdf/.docx/.txt present. `sanitize_filename()` handles path traversal. Files stored in org-isolated dirs. But: No content-type/magic-byte verification beyond extension. No malware/zip-bomb scanning.
- **Severity**: High
- **Fix needed**: Add content-type/magic-byte check, malware scanning

## Item 5: IDOR / BOLA
- **Verdict**: OK
- **Evidence**: Every route filtering by ID also filters by `current_user.organization_id`. Repo layer `get_by_id_and_org()` pattern for all tenant entities.
- **Severity**: Low
- **Fix needed**: —

## Item 6: Rate Limiting
- **Verdict**: NOT APPLICABLE
- **Evidence**: No rate limiting infrastructure (slowapi/limiter) found. `RequestTraceMiddleware` only adds trace IDs/timing. No per-IP or per-user limits on login/register/refresh/chat/upload.
- **Severity**: N/A
- **Fix needed**: Add rate limiting

## Item 7: JWT Secrets
- **Verdict**: PARTIAL
- **Evidence**: `SECRET_KEY`/`JWT_SECRET` have insecure defaults in `config.py`. Prod validator catches defaults but defaults exist in code. HS256 pinned. Refresh token rotation via Redis revocation.
- **Severity**: Medium
- **Fix needed**: Remove default secrets, enforce env vars

## Item 8: Exposed Secrets
- **Verdict**: CRITICAL
- **Evidence**: `.env` committed with real values: `SECRET_KEY`, `JWT_SECRET`, `OPENAI_API_KEY`. `docker-compose.yml` uses default `postgres/postgres`. `.env.example` has insecure defaults. Removed from code during Phase 2.
- **Severity**: Critical
- **Fix needed**: Removed secrets from repo, added to .gitignore

## Item 9: Password Hashing
- **Verdict**: OK
- **Evidence**: `bcrypt` used with `gensalt()` per-user salt. `checkpw()` constant-time compare. No md5/sha*. Default bcrypt cost.
- **Severity**: Low
- **Fix needed**: —

## Item 10: MFA
- **Verdict**: MISSING
- **Evidence**: No MFA/TOTP implementation. Only password-based auth. No 2FA flow, backup codes, or TOTP secrets.
- **Severity**: High
- **Fix needed**: Add TOTP for admin roles

## Item 11: CORS
- **Verdict**: PARTIAL
- **Evidence**: `ALLOWED_ORIGINS` explicit list (no "*") with credentials. Methods/headers minimal. But origins include production domain while default ENV="development".
- **Severity**: Medium
- **Fix needed**: Fix env/origin mismatch, restrict methods

## Item 12: Token Storage
- **Verdict**: VULNERABLE (Phase 2 fix applied)
- **Evidence**: Access tokens previously stored in `localStorage` in `authStore.ts` and `api/client.ts`. Vulnerable to XSS-induced token theft. Refresh flow used `localStorage`-stored refresh token. **FIXED**: Access tokens now stored in memory only; refresh tokens sent as HttpOnly Secure SameSite=strict cookies.
- **Severity**: Critical
- **Fix needed**: Removed from localStorage, added HttpOnly refresh cookie

## Item 13: Client-side-only Permissions
- **Verdict**: VULNERABLE (Phase 2 fix applied)
- **Evidence**: "Admin" nav link visible in React sidebar. Backend `require_role()` exists but NOT used on any route. Role/permission checks only client-side. **FIXED**: Backend guards enforced on all admin routes.
- **Severity**: High
- **Fix needed**: Added backend role checks on all privileged routes

## Item 14: Row-level Security
- **Verdict**: PARTIAL
- **Evidence**: All models have `organization_id` FK to `organizations.id` with `ondelete='CASCADE'`. All queries scoped by `org_id`. RAG searches org-scoped. But: PostgreSQL RLS not enabled. Only app-level isolation.
- **Severity**: Medium
- **Fix needed**: Enable PostgreSQL RLS as defense-in-depth

## Item 15: Webhooks
- **Verdict**: NOT APPLICABLE
- **Evidence**: No webhook receiver endpoints found. Integration `test_connection()` tests outbound connectivity but no inbound webhook HMAC verification.
- **Severity**: N/A
- **Fix needed**: —

## Item 16: SSRF
- **Verdict**: PARTIAL
- **Evidence**: Integration `test_connection()` makes outbound calls based on stored config. No URL allowlist/denylist for private IPs, localhost, 169.254.x.x, or cloud metadata. **FIXED**: URL validation added to integration service.
- **Severity**: High
- **Fix needed**: Added URL allowlist/denylist

## Item 17: Source Maps
- **Verdict**: PARTIAL
- **Evidence**: `vite.config.ts` doesn't set `sourcemap: false` for production. Default Vite generates sourcemaps. Could be served to end users in production build. **FIXED**: Production build configured to disable sourcemaps.
- **Severity**: Low
- **Fix needed**: Disabled sourcemaps for production

## Item 18: Default Credentials
- **Verdict**: CRITICAL (Phase 2 fix applied)
- **Evidence**: Login page prefilled with `admin@omnicorp.com` and `password`. `docker-compose.yml` used default `postgres/postgres`. `.env.example` had insecure defaults. **FIXED**: Removed all default values; `.env.example` uses `CHANGE_ME_IN_PRODUCTION` placeholders.
- **Severity**: Critical
- **Fix needed**: Removed defaults, documented required env vars

## Item 19: Sensitive Data in Logs
- **Verdict**: OK
- **Evidence**: structlog processors don't include passwords/tokens/PII. Middleware logs method/path/status/duration/request_id only. Exception handler logs error message/path but no secrets.
- **Severity**: Low
- **Fix needed**: —

## Item 20: Vulnerable Dependencies
- **Verdict**: OK / MODERATE
- **Evidence**: `pip-audit` backend: No known vulnerabilities. `npm audit --omit=dev` frontend: 2 moderate react-router vulns (CVE-2025-68470 open redirect bypass, GHSA-337j-9hxr-rhxr constructor injection). Updated react-router-dom.
- **Severity**: Medium
- **Fix needed**: Update dependencies regularly

---

## Other Risks Found

| Risk | Verdict | Evidence | Severity |
|------|---------|----------|----------|
| Prompt injection / approval bypass | PARTIAL | Agent execution flow could be manipulated; no explicit approval bypass protection beyond role/permission checks | Medium |
| Unauthenticated debug endpoints | PARTIAL | FastAPI `/docs` and `/redoc` exposed (should be disabled in production) | Medium |
| Missing security headers | CRITICAL | No HSTS, X-Content-Type-Options, X-Frame-Options, or CSP headers configured in FastAPI app | Critical |
| Verbose error messages | Medium | Exception details could leak internal info; currently caught by custom exception handler | Medium |

---

## GitHub Actions Security Pipeline

The following CI jobs are configured to run on every push and pull request:

1. **pip-audit**: Scans `backend/requirements.txt` for known High/Critical vulnerabilities
2. **npm audit --omit=dev**: Scans frontend dependencies for moderate+ vulnerabilities
3. **bandit -r backend/app -ll**: Runs Python security linter on backend code
4. **ruff check**: Lints backend Python code
5. **pytest**: Runs test suite
6. **TypeScript typecheck + Vite build**: Verifies frontend compiles without errors

Workflow files: `.github/workflows/ci.yml`, `.github/workflows/frontend-build.yml`