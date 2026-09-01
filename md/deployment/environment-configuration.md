# Deployment — Multi-Stage Environment Configuration

## Status
**Status:** ✅ IMPLEMENTED (Development, Staging & Production Profiles)

---

## 1. Environment Profiles Comparison

| Configuration Dimension | Development (`.env.dev`) | Staging (`.env.staging`) | Production (`.env.prod`) |
| :--- | :--- | :--- | :--- |
| **`DEBUG` Flag** | `true` | `false` | `false` |
| **Database Pool** | 5 connections | 15 connections | 30 connections + PgBouncer |
| **LLM Provider** | Local Ollama / GPT-4o-mini | Claude 3.5 Sonnet / GPT-4o | Claude 3.5 Sonnet + Local Fallback |
| **Object Storage** | MinIO Local | AWS S3 Bucket | AWS S3 Bucket (Multi-AZ Encrypted) |
| **Log Format** | Colorized Console | JSON Structured | JSON Structured -> Datadog / Elastic |
| **CORS Origins** | `http://localhost:3000` | `https://staging.omniagent.io` | `https://portal.omniagent.io` |
| **Rate Limiter** | 600 req/min | 120 req/min | 120 req/min per IP/Token |
