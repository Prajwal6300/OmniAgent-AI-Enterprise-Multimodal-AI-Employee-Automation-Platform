# Development — Local Development Guidelines & Commands

## Status
**Status:** ✅ IMPLEMENTED

---

## 1. Running the Full Multi-Service Stack Locally

```bash
# Terminal 1: Infrastructure Services (Postgres, pgvector, Redis, MinIO)
docker compose up postgres redis minio

# Terminal 2: FastAPI Backend Server
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 3: Celery Background Task Worker
cd backend
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info -Q default,bulk_ingestion,high_priority

# Terminal 4: Next.js Frontend Portal
cd frontend
npm run dev
```

---

## 2. Database Seeds & Testing Data
```bash
# Run database seed script to generate default admin user and mock documents
python backend/scripts/seed_db.py
```
* **Default Admin Account:** `admin@omniagent.io`
* **Default Password:** `AdminEnterprise2026!`
