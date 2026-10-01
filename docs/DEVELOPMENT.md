# OmniAgent AI — Local Development & Contributing Guide

## 1. Prerequisites
- **Python**: 3.11 or 3.13
- **Node.js**: 20+ and npm
- **Docker & Docker Compose**: For local PostgreSQL + `pgvector` and Redis services
- **Git**

---

## 2. Quickstart Local Setup

### 1. Clone & Configure Environment
```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

### 2. Start Supporting Services via Docker Compose
```bash
docker compose up -d postgres redis
```
This boots:
- PostgreSQL 16 with `pgvector` on port `5432`
- Redis 7 on port `6379`

### 3. Setup Python Backend Environment
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 4. Setup Frontend Development Server
```bash
cd frontend
npm install
npm run dev
```
The Vite development server will start on `http://localhost:5173`.

---

## 3. Running Tests & Linters

### Backend Tests
```bash
# Run entire test suite (unit, integration, security, e2e)
python -m pytest

# Run with verbose output and coverage
python -m pytest -v
```

### Code Formatting & Linting
```bash
# Check code style and errors
python -m ruff check .

# Automatically apply safe fixes
python -m ruff check . --fix
```

### Frontend Typechecking & Production Build
```bash
npm --prefix frontend run build
```

---

## 4. Architectural Rules & Standards
1. **Multi-Tenancy**: Every database table, query, and storage key must explicitly enforce `organization_id`.
2. **Zero Mocks in Production**: Production code under `backend/app/` must never import test fixtures or mock modules. Tests must use `backend/tests/fixtures/`.
3. **Fail-Fast Configuration**: Settings must validate environment consistency at startup.
4. **No Direct Git Pushes**: Development is performed on feature branches and committed using Conventional Commits.
