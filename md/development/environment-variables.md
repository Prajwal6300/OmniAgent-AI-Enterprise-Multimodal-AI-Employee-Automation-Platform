# Development — Complete Environment Variables Reference

## Status
**Status:** ✅ IMPLEMENTED (.env Configuration Template)

---

## 1. Environment Configuration Matrix

```env
# ==========================================
# 1. CORE APPLICATION SETTINGS
# ==========================================
ENVIRONMENT=development                # development | staging | production
DEBUG=true
PROJECT_NAME="OmniAgent AI"
API_V1_STR=/api/v1
SECRET_KEY=<YOUR_SUPER_SECRET_HMAC_KEY_MIN_32_CHARS>
JWT_SECRET=<YOUR_JWT_SECRET_KEY>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# ==========================================
# 2. DATABASE & CACHE
# ==========================================
POSTGRES_USER=omni_admin
POSTGRES_PASSWORD=<YOUR_POSTGRES_PASSWORD>
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=omniagent_db
DATABASE_URL=postgresql+asyncpg://omni_admin:<YOUR_POSTGRES_PASSWORD>@localhost:5432/omniagent_db

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

# ==========================================
# 3. OBJECT STORAGE (S3 / MINIO)
# ==========================================
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=<YOUR_MINIO_ACCESS_KEY>
S3_SECRET_KEY=<YOUR_MINIO_SECRET_KEY>
S3_BUCKET_NAME=omni-enterprise-artifacts
S3_REGION=us-east-1
S3_USE_SSL=false

# ==========================================
# 4. FOUNDATION LLM PROVIDERS
# ==========================================
OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
ANTHROPIC_API_KEY=<YOUR_ANTHROPIC_API_KEY>
GOOGLE_API_KEY=<YOUR_GOOGLE_GEMINI_API_KEY>
OLLAMA_BASE_URL=http://localhost:11434

# ==========================================
# 5. EMBEDDING & VECTOR RETRIEVAL
# ==========================================
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_DIMENSION=1024
RERANKER_MODEL=BAAI/bge-reranker-large
TOP_K_RETRIEVAL=50
TOP_K_RERANKED=5

# ==========================================
# 6. EXTERNAL CONNECTORS & NOTIFICATIONS
# ==========================================
TAVILY_API_KEY=<YOUR_TAVILY_API_KEY>
SLACK_WEBHOOK_URL=<YOUR_SLACK_WEBHOOK_URL>
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<YOUR_SENDGRID_KEY>
SMTP_FROM_EMAIL=notifications@omniagent.io

# ==========================================
# 7. OBSERVABILITY & TELEMETRY
# ==========================================
PROMETHEUS_METRICS_ENABLED=true
SENTRY_DSN=<YOUR_SENTRY_DSN_OPTIONAL>
LOG_LEVEL=INFO
```
