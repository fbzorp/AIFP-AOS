#!/bin/bash
# PostgreSQL database restore script for AIFP-AOS
# Usage: ./scripts/restore_db.sh <backup_file>

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 backups/aifp_backup_20260731_120000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "Starting database restore from ${BACKUP_FILE} at $(date)"

# Decompress if gzipped
if [[ "${BACKUP_FILE}" == *.gz ]]; then
    TEMP_SQL=$(mktemp)
    gunzip -c "${BACKUP_FILE}" > "${TEMP_SQL}"
    RESTORE_FILE="${TEMP_SQL}"
else
    RESTORE_FILE="${BACKUP_FILE}"
fi

# Confirm before restore
read -p "This will drop and recreate the database. Continue? (yes/no): " CONFIRM
if [ "${CONFIRM}" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Drop existing database
echo "Dropping existing database..."
docker compose -f docker-compose.dev.yml exec -T postgres psql -U aifp -d postgres -c "DROP DATABASE IF EXISTS aifp_dev;"

# Create fresh database
echo "Creating fresh database..."
docker compose -f docker-compose.dev.yml exec -T postgres psql -U aifp -d postgres -c "CREATE DATABASE aifp_dev;"

# Restore from backup
echo "Restoring from backup..."
docker compose -f docker-compose.dev.yml exec -T postgres psql -U aifp -d aifp_dev < "${RESTORE_FILE}"

# Clean up temp file
if [ -n "${TEMP_SQL}" ]; then
    rm "${TEMP_SQL}"
fi

echo "Restore completed at $(date)"

# Verify restore
echo "Verifying restore..."
ROW_COUNT=$(docker compose -f docker-compose.dev.yml exec -T postgres psql -U aifp -d aifp_dev -t -c "SELECT COUNT(*) FROM audit_events;")
echo "Audit events count: ${ROW_COUNT}"