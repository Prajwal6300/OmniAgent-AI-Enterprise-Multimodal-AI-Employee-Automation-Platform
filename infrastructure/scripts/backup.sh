#!/usr/bin/env bash
set -e
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"
echo "Starting PostgreSQL backup..."
docker exec -t omniagent-postgres pg_dumpall -c -U postgres > "$BACKUP_DIR/omniagent_db_$TIMESTAMP.sql"
echo "Backup saved to $BACKUP_DIR/omniagent_db_$TIMESTAMP.sql"
