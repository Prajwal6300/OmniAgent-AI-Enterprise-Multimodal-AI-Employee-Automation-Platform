#!/usr/bin/env bash
set -e
echo "Running lint checks..."
ruff check backend
cd frontend && npm run build
