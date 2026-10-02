.PHONY: help setup dev dev-backend dev-frontend test lint format migrate seed docker-up docker-down clean

help:
	@echo "OmniAgent AI Development Commands:"
	@echo "  make setup         Install all backend and frontend dependencies"
	@echo "  make dev           Start infrastructure containers and print commands"
	@echo "  make dev-backend   Start FastAPI server with auto-reload"
	@echo "  make dev-frontend  Start Vite React frontend"
	@echo "  make test          Run pytest suite across backend"
	@echo "  make lint          Run ruff and frontend build check"
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
	docker compose up -d postgres redis
	@echo "Start backend: cd backend && uvicorn app.main:app --reload"
	@echo "Start frontend: cd frontend && npm run dev"

test:
	pytest backend/tests/ -v

lint:
	ruff check backend
	cd frontend && npm run build

format:
	ruff format backend

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
