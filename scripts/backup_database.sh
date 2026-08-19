#!/bin/bash
# Automated database backup script for AIFP-AOS
# This script creates daily backups with retention policies

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
DB_NAME="${POSTGRES_DB:-aifp_prod}"
DB_USER="${POSTGRES_USER:-aifp}"
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/aifp_backup_${TIMESTAMP}.sql.gz"
LOG_FILE="${PROJECT_DIR}/logs/aifp_backup.log"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"
mkdir -p "$(dirname "${LOG_FILE}")"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting backup process"

# Perform backup
log "Creating backup: ${BACKUP_FILE}"
cd "${PROJECT_DIR}"

# Determine which compose file to use
COMPOSE_FILE="docker-compose.prod.yml"
if [ ! -f "${COMPOSE_FILE}" ]; then
    COMPOSE_FILE="docker-compose.dev.yml"
fi

if docker compose -f "${COMPOSE_FILE}" exec -T postgres pg_dump -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}" | gzip > "${BACKUP_FILE}"; then
    log "Backup created successfully: ${BACKUP_FILE}"
    
    # Get backup size
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    log "Backup size: ${BACKUP_SIZE}"
    
    # Remove old backups (retention policy)
    log "Cleaning up backups older than ${RETENTION_DAYS} days"
    find "${BACKUP_DIR}" -name "aifp_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
    
    # Count remaining backups
    BACKUP_COUNT=$(find "${BACKUP_DIR}" -name "aifp_backup_*.sql.gz" | wc -l)
    log "Total backups after cleanup: ${BACKUP_COUNT}"
    
    log "Backup process completed successfully"
    exit 0
else
    log "ERROR: Backup failed"
    exit 1
fi