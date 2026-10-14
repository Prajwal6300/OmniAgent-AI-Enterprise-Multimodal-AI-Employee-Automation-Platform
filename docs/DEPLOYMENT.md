# OmniAgent AI — Production Deployment Guide

This guide details step-by-step deployment of OmniAgent AI to the fixed production stack: **Neon** (PostgreSQL + pgvector + Cloudflare R2 Storage), **Render** (Backend Docker Web Service + Celery Worker), and **Vercel** (Frontend SPA).

---

## 1. Ordered Deployment Procedure

```
  Step 1: Neon Setup (PostgreSQL, pgvector, R2 Bucket)
             │
             ▼
  Step 2: Render Backend & Workers (Web API, Worker, Redis)
             │
             ▼
  Step 3: Run Database Migrations (`alembic upgrade head`)
             │
             ▼
  Step 4: Vercel Frontend Deployment
             │
             ▼
  Step 5: Configure CORS (`ALLOWED_ORIGINS`) & Smoke Test
```

---

## 2. Step-by-Step Instructions

### Step 1: Provision Neon
1. Create a new Neon project in your preferred AWS region.
2. In the **SQL Editor**, enable `pgvector`:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Navigate to **Storage** and create a private bucket using Cloudflare R2 compatible settings.
4. Generate **R2 Access Keys** under **Neon Dashboard -> Storage**. Save the `Access Key ID` and `Secret Access Key`.

### Step 2: Provision Render Infrastructure
1. In the **Render Dashboard**, create a **Redis Key Value** service. Save the internal connection URL.
2. Create a new **Web Service** pointing to this repository:
   - **Environment**: Docker
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Docker Context**: Root of repository
3. Set the environment variables in Render (see table below).
4. Create a **Background Worker** with the same Docker image and command:
   ```bash
   celery -A app.workers worker --loglevel=info
   ```

### Step 3: Run Database Migrations
Using the direct database session URL (port 5432), run:
```bash
alembic upgrade head
```

### Step 4: Deploy Frontend to Vercel
1. Import the repository into Vercel.
2. Set **Root Directory** to `frontend`.
3. Set Environment Variable `VITE_API_BASE_URL` to your Render Web Service URL with `/api/v1` suffix (e.g. `https://omniagent-api.onrender.com/api/v1`).
4. Click **Deploy**.

### Step 5: Update CORS & Run Smoke Test
1. In the Render Web Service settings, update `ALLOWED_ORIGINS` to include your Vercel URL:
   ```json
   ["https://your-omniagent-app.vercel.app"]
   ```
2. Verify system health:
   ```bash
   curl -f https://your-omniagent-api.onrender.com/api/v1/health
   curl -f https://your-omniagent-api.onrender.com/api/v1/ready
   ```

---

## 3. Production Environment Variables Reference

| Variable Name | Description | Where to Get It | Where to Set It |
|---|---|---|---|
| `ENVIRONMENT` | Must be `production` | Set manually | Render Web & Worker |
| `SECRET_KEY` | Min 32-char cryptographic random secret | `openssl rand -hex 32` | Render Web & Worker |
| `JWT_SECRET` | Min 32-char secret (must differ from SECRET_KEY) | `openssl rand -hex 32` | Render Web & Worker |
| `ENCRYPTION_KEY` | 32-character encryption key for credentials | `openssl rand -hex 32` | Render Web & Worker |
| `DATABASE_URL` | Neon Postgres connection URL | Neon Dashboard -> Database | Render Web & Worker |
| `ALEMBIC_DATABASE_URL` | Neon Direct Session connection | Neon Dashboard -> Database | Migration runner |
| `REDIS_URL` | Redis instance URL | Render Redis Internal URL | Render Web & Worker |
| `OPENAI_API_KEY` | OpenAI API Key (`sk-...`) | OpenAI Developer Platform | Render Web & Worker |
| `STORAGE_PROVIDER` | Must be `s3` (Cloudflare R2) | Set manually | Render Web & Worker |
| `S3_ENDPOINT` | R2 endpoint URL (e.g. `https://<account>.r2.cloudflare.com`) | Neon Dashboard -> Storage | Render Web & Worker |
| `S3_REGION` | R2 region (e.g. `auto`) | Neon Dashboard -> Storage | Render Web & Worker |
| `S3_ACCESS_KEY` | R2 Access Key ID | Neon Dashboard -> Storage | Render Web & Worker |
| `S3_SECRET_KEY` | R2 Secret Access Key | Neon Dashboard -> Storage | Render Web & Worker |
| `S3_BUCKET` | Default `documents` | Neon Dashboard -> Storage | Render Web & Worker |
| `ALLOWED_ORIGINS` | JSON list of allowed origins | Vercel Deployment URL | Render Web |
| `VITE_API_BASE_URL` | Base API URL | Render Web Service URL | Vercel Frontend |
