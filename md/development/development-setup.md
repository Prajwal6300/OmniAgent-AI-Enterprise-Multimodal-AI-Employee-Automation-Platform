# Development — Local Development Setup & Prerequisites

## Status
**Status:** ✅ IMPLEMENTED (Standard Dev Toolchain)

---

## 1. Prerequisites & Required Tooling

* **Operating System:** Windows 10/11 (PowerShell / WSL2), macOS 13+, or Ubuntu 22.04 LTS
* **Python Runtime:** Python 3.11+ (with `pip`, `venv` or `poetry`)
* **Node.js Runtime:** Node.js 20 LTS (with `npm` or `pnpm`)
* **Container Engine:** Docker Desktop 24+ & Docker Compose v2
* **Database & Vector:** PostgreSQL 16 with `pgvector`
* **In-Memory Cache:** Redis 7+
* **System Utilities:** Tesseract OCR 5.3+, FFmpeg 6.0+, Git 2.40+

---

## 2. Step-by-Step Installation

### 1. Clone the Repository
```bash
git clone https://github.com/enterprise/omniagent-ai.git
cd omniagent-ai
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your LLM API keys, Database URLs, and secrets
```

### 3. Spin Up Infrastructure via Docker Compose
```bash
docker compose up -d postgres redis minio
```

### 4. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 5. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
# Portal accessible at http://localhost:3000
```
