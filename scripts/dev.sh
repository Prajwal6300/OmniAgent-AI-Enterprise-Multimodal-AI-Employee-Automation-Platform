#!/usr/bin/env bash
echo "Starting OmniAgent AI services..."
docker compose up -d postgres redis minio
echo "Services active. In separate terminals, run:"
echo "1. cd backend && uvicorn app.main:app --reload"
echo "2. cd frontend && npm run dev"
