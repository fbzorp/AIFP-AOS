#!/bin/bash
# Setup script for automated backup system
# This script configures backup automation for the project

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"

echo "Setting up automated backup system for AIFP-AOS..."

# Make scripts executable
chmod +x "${SCRIPT_DIR}/backup_database.sh"
chmod +x "${SCRIPT_DIR}/restore_database.sh"
chmod +x "${SCRIPT_DIR}/monitor_backups.sh"

echo "✓ Made backup scripts executable"

# Create backup directory
mkdir -p "${PROJECT_DIR}/backups"

echo "✓ Created backup directory: ${PROJECT_DIR}/backups"

# Create log directory
mkdir -p "${PROJECT_DIR}/logs"

echo "✓ Created log directory: ${PROJECT_DIR}/logs"

# Create log files
touch "${PROJECT_DIR}/logs/aifp_backup.log"
touch "${PROJECT_DIR}/logs/aifp_restore.log"
touch "${PROJECT_DIR}/logs/aifp_backup_monitor.log"

echo "✓ Created log files"

# Test backup script
echo ""
echo "Testing backup script..."
"${SCRIPT_DIR}/backup_database.sh"

if [ $? -eq 0 ]; then
    echo "✓ Backup test successful"
    
    # Show backup info
    LATEST_BACKUP=$(find "${PROJECT_DIR}/backups" -name "aifp_backup_*.sql.gz" -type f | sort -r | head -1)
    if [ -n "${LATEST_BACKUP}" ]; then
        BACKUP_SIZE=$(du -h "${LATEST_BACKUP}" | cut -f1)
        echo "✓ Latest backup: ${LATEST_BACKUP} (${BACKUP_SIZE})"
    fi
else
    echo "✗ Backup test failed"
    exit 1
fi

echo ""
echo "Backup automation setup complete!"
echo ""
echo "Manual commands:"
echo "  - Run backup: ${SCRIPT_DIR}/backup_database.sh"
echo "  - Restore database: ${SCRIPT_DIR}/restore_database.sh <backup_file>"
echo "  - Monitor backup health: ${SCRIPT_DIR}/monitor_backups.sh"
echo "  - View backup logs: tail -f ${PROJECT_DIR}/logs/aifp_backup.log"
echo ""
echo "For production automation:"
echo "  - Add backup_database.sh to cron/systemd scheduler"
echo "  - Add monitor_backups.sh to daily health checks"
echo ""
echo "Backups will be stored in: ${PROJECT_DIR}/backups"
echo "Retention policy: 7 days"
echo "Logs will be stored in: ${PROJECT_DIR}/logs"