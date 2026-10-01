#!/usr/bin/env bash
# ==============================================================================
# OmniAgent AI — Automated Postgres Database Restore Script
# Restores a compressed pg_dump file to the target database.
# ==============================================================================

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <path_to_backup_file.dump>"
    exit 1
fi

BACKUP_FILE="$1"

if [[ ! -f "${BACKUP_FILE}" ]]; then
    echo "ERROR: Backup file '${BACKUP_FILE}' does not exist."
    exit 1
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "ERROR: DATABASE_URL environment variable is required."
    exit 1
fi

echo "WARNING: Restoring will overwrite existing data in target database."
read -p "Are you sure you want to proceed? (yes/no): " CONFIRM
if [[ "${CONFIRM}" != "yes" ]]; then
    echo "Restore aborted by user."
    exit 0
fi

# Strip asyncpg/driver prefix if present for pg_restore
PG_URI="${DATABASE_URL/postgresql+asyncpg:\/\//postgres:\/\/}"

echo "Restoring database from ${BACKUP_FILE}..."
pg_restore --clean --if-exists --no-owner --no-privileges -d "${PG_URI}" "${BACKUP_FILE}"

echo "Database restore completed successfully."
