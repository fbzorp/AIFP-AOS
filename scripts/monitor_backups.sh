#!/bin/bash
# Backup monitoring script for AIFP-AOS
# This script checks backup status and logs failures

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
MAX_AGE_HOURS=26  # Maximum age of backup in hours (slightly more than 24h)
LOG_FILE="${PROJECT_DIR}/logs/backup_monitor.log"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"
mkdir -p "$(dirname "${LOG_FILE}")"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting backup monitoring check"

# Find most recent backup
LATEST_BACKUP=$(find "${BACKUP_DIR}" -name "aifp_backup_*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2)

if [ -z "$LATEST_BACKUP" ]; then
    log "ERROR: No backups found in ${BACKUP_DIR}"
    # In production, this would trigger an alert
    exit 1
fi

# Check backup age
BACKUP_AGE_SECONDS=$(($(date +%s) - $(stat -c %Y "$LATEST_BACKUP" 2>/dev/null || stat -c %Y "$LATEST_BACKUP")))
BACKUP_AGE_HOURS=$((BACKUP_AGE_SECONDS / 3600))

log "Latest backup: $(basename "$LATEST_BACKUP")"
log "Backup age: ${BACKUP_AGE_HOURS} hours"

if [ "$BACKUP_AGE_HOURS" -gt "$MAX_AGE_HOURS" ]; then
    log "ERROR: Backup is too old (${BACKUP_AGE_HOURS} hours > ${MAX_AGE_HOURS} hours)"
    # In production, this would trigger an alert
    exit 1
fi

# Check backup file integrity
if gzip -t "$LATEST_BACKUP" 2>/dev/null; then
    log "Backup file integrity check passed"
else
    log "ERROR: Backup file is corrupted"
    # In production, this would trigger an alert
    exit 1
fi

# Count total backups
BACKUP_COUNT=$(find "${BACKUP_DIR}" -name "aifp_backup_*.sql.gz" | wc -l)
log "Total backups: ${BACKUP_COUNT}"

log "Backup monitoring check completed successfully"
exit 0