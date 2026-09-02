#!/usr/bin/env bash
set -e
echo "Formatting codebase..."
ruff format backend agents automation multimodal tools tests
