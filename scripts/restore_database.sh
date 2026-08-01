#!/bin/bash
# Database restoration script for AIFP-AOS
# This script restores a database from a backup file

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
BACKUP_DIR="${PROJECT_DIR}/backups"
DB_NAME="aifp_dev"
DB_USER="aifp"
LOG_FILE="${PROJECT_DIR}/logs/aifp_restore.log"

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo "Available backups:"
    ls -lh "${BACKUP_DIR}"/aifp_backup_*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"
}

log "Starting restore process from: ${BACKUP_FILE}"

# Confirm restoration
read -p "This will DROP and RECREATE the database. Are you sure? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    log "Restore cancelled by user"
    exit 0
fi

# Stop application services
log "Stopping application services"
cd "${PROJECT_DIR}"
docker compose -f docker-compose.dev.yml stop api worker

# Perform restoration
log "Restoring database from: ${BACKUP_FILE}"
if gunzip -c "${BACKUP_FILE}" | docker compose -f docker-compose.dev.yml exec -T postgres psql -U "${DB_USER}" -d "${DB_NAME}"; then
    log "Database restored successfully from: ${BACKUP_FILE}"
    
    # Restart application services
    log "Restarting application services"
    docker compose -f docker-compose.dev.yml start api worker
    
    log "Restore process completed successfully"
    exit 0
else
    log "ERROR: Restore failed"
    
    # Attempt to restart services even if restore failed
    log "Attempting to restart application services"
    docker compose -f docker-compose.dev.yml start api worker
    
    exit 1
fi