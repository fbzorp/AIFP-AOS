#!/bin/bash
# PostgreSQL database backup script for AIFP-AOS
# Usage: ./scripts/backup_db.sh

set -e

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/aifp_backup_${TIMESTAMP}.sql"
RETENTION_DAYS=7

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

echo "Starting database backup at $(date)"

# Run pg_dump using docker compose
docker compose -f docker-compose.dev.yml exec -T postgres pg_dump -U aifp aifp_dev > "${BACKUP_FILE}"

# Compress the backup
gzip "${BACKUP_FILE}"
BACKUP_FILE="${BACKUP_FILE}.gz"

echo "Backup completed: ${BACKUP_FILE}"

# Remove old backups (retention policy)
find "${BACKUP_DIR}" -name "aifp_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete

echo "Old backups removed (retention: ${RETENTION_DAYS} days)"
echo "Backup process completed at $(date)"