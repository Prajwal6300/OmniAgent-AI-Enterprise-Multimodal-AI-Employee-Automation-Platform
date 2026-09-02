#!/usr/bin/env bash
set -e
echo "Running Alembic migrations..."
cd backend
alembic upgrade head
