.PHONY: help setup dev dev-backend dev-frontend test lint format migrate seed docker-up docker-down clean

help:
	@echo "OmniAgent AI Development Commands:"
	@echo "  make setup         Install all backend and frontend dependencies"
	@echo "  make dev           Start both backend and frontend development servers"
	@echo "  make dev-backend   Start FastAPI server with auto-reload"
	@echo "  make dev-frontend  Start Vite React frontend"
	@echo "  make test          Run test suite across backend, agents, and automation"
	@echo "  make lint          Run ruff and eslint"
	@echo "  make format        Run formatting tools"
	@echo "  make migrate       Run database migrations"
	@echo "  make seed          Seed database with development data"
	@echo "  make docker-up     Start infrastructure containers via Docker Compose"
	@echo "  make docker-down   Stop infrastructure containers"

setup:
	python -m pip install -r backend/requirements.txt
	cd frontend && npm install

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

dev:
	docker compose up -d postgres redis minio
	@echo "Start backend: uvicorn app.main:app --reload (in backend/)"
	@echo "Start frontend: npm run dev (in frontend/)"

test:
	pytest tests/ -v

lint:
	ruff check backend agents automation multimodal tools tests
	cd frontend && npm run lint

format:
	ruff format backend agents automation multimodal tools tests

migrate:
	cd backend && alembic upgrade head

seed:
	python scripts/seed.py

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
