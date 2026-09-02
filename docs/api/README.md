# API Architecture & Conventions

All endpoints follow RESTful standards under `/api/v1/` prefix with unified JSON envelope formats.

## Key Principles
- **Authentication**: Bearer JWT via Authorization header.
- **Envelope Standard**: Predictable structure with `success`, `data`, and `error` objects.
- **Error Standard**: RFC 7807 problem details.
- **Rate Limiting**: Redis token bucket per tenant and IP.
