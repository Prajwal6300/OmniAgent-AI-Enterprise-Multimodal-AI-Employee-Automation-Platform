#!/usr/bin/env bash
set -e
echo "Deploying OmniAgent AI stack..."
docker compose pull
docker compose up -d --remove-orphans
echo "Deployment successful."
