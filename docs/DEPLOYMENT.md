# OmniAgent AI — Production Deployment Guide

This guide details step-by-step deployment of OmniAgent AI to the fixed production stack: **Supabase** (PostgreSQL + pgvector + Storage), **Render** (Backend Docker Web Service + Celery Worker), and **Vercel** (Frontend SPA).

---

## 1. Ordered Deployment Procedure

```
  Step 1: Supabase Setup (Database, pgvector, Storage Bucket)
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

### Step 1: Provision Supabase
1. Create a new Supabase project in your preferred AWS region.
2. In the **SQL Editor**, enable `pgvector`:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Navigate to **Storage** and create a private bucket named `documents`.
4. Generate **S3 Access Keys** under **Project Settings -> Storage -> S3 Access Keys**. Save the `Access Key ID` and `Secret Access Key`.

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
| `DATABASE_URL` | Supabase Postgres Transaction Pooler (port 6543) | Supabase Dashboard -> Database | Render Web & Worker |
| `ALEMBIC_DATABASE_URL` | Supabase Direct Session connection (port 5432) | Supabase Dashboard -> Database | Migration runner |
| `REDIS_URL` | Redis instance URL | Render Redis Internal URL | Render Web & Worker |
| `OPENAI_API_KEY` | OpenAI API Key (`sk-...`) | OpenAI Developer Platform | Render Web & Worker |
| `STORAGE_PROVIDER` | Must be `supabase` in production | Set manually | Render Web & Worker |
| `SUPABASE_S3_ENDPOINT`| S3 API endpoint URL | Supabase Dashboard -> Storage | Render Web & Worker |
| `SUPABASE_S3_REGION` | S3 region (e.g. `us-east-1`) | Supabase Dashboard -> Storage | Render Web & Worker |
| `SUPABASE_S3_ACCESS_KEY` | Storage S3 Access Key ID | Supabase Dashboard -> Storage | Render Web & Worker |
| `SUPABASE_S3_SECRET_KEY` | Storage S3 Secret Access Key | Supabase Dashboard -> Storage | Render Web & Worker |
| `SUPABASE_BUCKET` | Default `documents` | Supabase Dashboard -> Storage | Render Web & Worker |
| `ALLOWED_ORIGINS` | JSON list of allowed origins | Vercel Deployment URL | Render Web |
| `VITE_API_BASE_URL` | Base API URL | Render Web Service URL | Vercel Frontend |
