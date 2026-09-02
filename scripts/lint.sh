#!/usr/bin/env bash
set -e
echo "Running lint checks..."
ruff check backend agents automation multimodal tools tests
cd frontend && npm run lint
