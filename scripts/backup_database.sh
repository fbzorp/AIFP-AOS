#!/bin/bash
# Automated database backup script for AIFP-AOS
# This script creates daily backups with retention policies

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
BACKUP_DIR="${PROJECT_DIR}/backups"
RETENTION_DAYS=7
DB_NAME="aifp_dev"
DB_USER="aifp"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/aifp_backup_${TIMESTAMP}.sql.gz"
LOG_FILE="${PROJECT_DIR}/logs/aifp_backup.log"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"
mkdir -p "$(dirname "${LOG_FILE}")"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"
}

log "Starting backup process"

# Perform backup
log "Creating backup: ${BACKUP_FILE}"
cd "${PROJECT_DIR}"
if docker compose -f docker-compose.dev.yml exec -T postgres pg_dump -U "${DB_USER}" -d "${DB_NAME}" | gzip > "${BACKUP_FILE}"; then
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