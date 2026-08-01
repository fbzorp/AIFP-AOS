#!/bin/bash
# Backup monitoring and health check script
# This script checks backup health and sends alerts if needed

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
BACKUP_DIR="${PROJECT_DIR}/backups"
RETENTION_DAYS=7
MIN_BACKUP_SIZE_KB=100  # Minimum backup size in KB
LOG_FILE="${PROJECT_DIR}/logs/aifp_backup_monitor.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"
}

log "Starting backup health check"

# Check if backup directory exists
if [ ! -d "${BACKUP_DIR}" ]; then
    log "ERROR: Backup directory does not exist: ${BACKUP_DIR}"
    # Send alert (placeholder - implement email/slack notification)
    log "ALERT: Backup directory missing"
    exit 1
fi

# Check for recent backups
LATEST_BACKUP=$(find "${BACKUP_DIR}" -name "aifp_backup_*.sql.gz" -type f -mtime -1 | sort -r | head -1)

if [ -z "${LATEST_BACKUP}" ]; then
    log "WARNING: No backup found in the last 24 hours"
    # Send alert
    log "ALERT: No recent backup found"
    exit 1
fi

log "Latest backup: ${LATEST_BACKUP}"

# Check backup size
BACKUP_SIZE_KB=$(du -k "${LATEST_BACKUP}" | cut -f1)
if [ "${BACKUP_SIZE_KB}" -lt "${MIN_BACKUP_SIZE_KB}" ]; then
    log "WARNING: Backup size too small: ${BACKUP_SIZE_KB} KB (minimum: ${MIN_BACKUP_SIZE_KB} KB)"
    # Send alert
    log "ALERT: Backup size suspiciously small"
    exit 1
fi

log "Backup size OK: ${BACKUP_SIZE_KB} KB"

# Check backup integrity (try to decompress)
if ! gunzip -t "${LATEST_BACKUP}"; then
    log "ERROR: Backup file is corrupted"
    # Send alert
    log "ALERT: Backup file corrupted"
    exit 1
fi

log "Backup integrity OK"

# Count total backups
BACKUP_COUNT=$(find "${BACKUP_DIR}" -name "aifp_backup_*.sql.gz" | wc -l)
log "Total backups: ${BACKUP_COUNT}"

# Check retention policy compliance
OLD_BACKUPS=$(find "${BACKUP_DIR}" -name "aifp_backup_*.sql.gz" -mtime +${RETENTION_DAYS} | wc -l)
if [ "${OLD_BACKUPS}" -gt 0 ]; then
    log "WARNING: ${OLD_BACKUPS} backups older than ${RETENTION_DAYS} days found"
    # Send alert
    log "ALERT: Retention policy not enforced"
else
    log "Retention policy OK"
fi

log "Backup health check completed successfully"
exit 0