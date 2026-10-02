#!/usr/bin/env bash
echo "Starting OmniAgent AI services..."
docker compose up -d postgres redis
echo "Services active. In separate terminals, run:"
echo "1. cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "2. cd frontend && npm run dev"
