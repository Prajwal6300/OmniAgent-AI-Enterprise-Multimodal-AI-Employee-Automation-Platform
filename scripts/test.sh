#!/usr/bin/env bash
set -e
echo "Running OmniAgent AI test suite..."
pytest tests/ -v
