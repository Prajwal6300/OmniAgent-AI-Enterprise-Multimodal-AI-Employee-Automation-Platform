#!/usr/bin/env bash
# ==============================================================================
# OmniAgent AI — Automated Postgres Database Backup Script
# Creates a compressed, timestamped pg_dump of the production database.
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/omniagent_backup_${TIMESTAMP}.dump"

if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "ERROR: DATABASE_URL environment variable is required."
    exit 1
fi

mkdir -p "${BACKUP_DIR}"

echo "Starting OmniAgent AI database backup to ${BACKUP_FILE}..."

# Strip asyncpg/driver prefix if present for standard pg_dump
PG_URI="${DATABASE_URL/postgresql+asyncpg:\/\//postgres:\/\/}"

pg_dump -Fc --no-owner --no-privileges -d "${PG_URI}" -f "${BACKUP_FILE}"

echo "Backup completed successfully: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))"

# Retention: keep last 14 backups
find "${BACKUP_DIR}" -name "omniagent_backup_*.dump" -type f -mtime +14 -delete
