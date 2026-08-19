#!/bin/bash
# Automated restore test script for AIFP-AOS
# This script tests the backup and restore functionality

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
DB_NAME="${POSTGRES_DB:-aifp_prod}"
DB_USER="${POSTGRES_USER:-aifp}"
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEST_BACKUP_FILE="${BACKUP_DIR}/test_restore_${TIMESTAMP}.sql.gz"
LOG_FILE="${PROJECT_DIR}/logs/test_restore.log"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"
mkdir -p "$(dirname "${LOG_FILE}")"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting restore test process"

# Determine which compose file to use
COMPOSE_FILE="docker-compose.prod.yml"
if [ ! -f "${COMPOSE_FILE}" ]; then
    COMPOSE_FILE="docker-compose.dev.yml"
fi

# Step 1: Create a test backup
log "Step 1: Creating test backup"
docker compose -f "${COMPOSE_FILE}" exec -T postgres pg_dump -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}" | gzip > "${TEST_BACKUP_FILE}"
log "Test backup created: ${TEST_BACKUP_FILE}"

# Step 2: Create a test row
log "Step 2: Creating test row in database"
docker compose -f "${COMPOSE_FILE}" exec -T postgres psql -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}" -c "
INSERT INTO agents (id, name, role, status) 
VALUES ('test-restore-001', 'Test Restore Agent', 'test', 'active')
ON CONFLICT (id) DO UPDATE SET name = 'Test Restore Agent', role = 'test', status = 'active';
"

# Step 3: Verify test row exists
log "Step 3: Verifying test row exists"
TEST_ROW_COUNT=$(docker compose -f "${COMPOSE_FILE}" exec -T postgres psql -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}" -tAc "SELECT COUNT(*) FROM agents WHERE id = 'test-restore-001'")
log "Test row count before modification: ${TEST_ROW_COUNT}"

if [ "$TEST_ROW_COUNT" -ne 1 ]; then
    log "ERROR: Test row not found or multiple rows found"
    exit 1
fi

# Step 4: Modify the test row
log "Step 4: Modifying test row"
docker compose -f "${COMPOSE_FILE}" exec -T postgres psql -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}" -c "
UPDATE agents SET name = 'Test Restore Agent - MODIFIED' WHERE id = 'test-restore-001';
"

# Step 5: Verify modification
log "Step 5: Verifying modification"
MODIFIED_NAME=$(docker compose -f "${COMPOSE_FILE}" exec -T postgres psql -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}" -tAc "SELECT name FROM agents WHERE id = 'test-restore-001'")
log "Modified name: ${MODIFIED_NAME}"

if [ "$MODIFIED_NAME" != "Test Restore Agent - MODIFIED" ]; then
    log "ERROR: Modification failed"
    exit 1
fi

# Step 6: Restore from backup
log "Step 6: Restoring from backup"
docker compose -f "${COMPOSE_FILE}" exec -T postgres psql -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}" < <(gunzip -c "${TEST_BACKUP_FILE}")
log "Restore completed"

# Step 7: Verify test row is recovered
log "Step 7: Verifying test row is recovered"
RECOVERED_NAME=$(docker compose -f "${COMPOSE_FILE}" exec -T postgres psql -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}" -tAc "SELECT name FROM agents WHERE id = 'test-restore-001'")
log "Recovered name: ${RECOVERED_NAME}"

if [ "$RECOVERED_NAME" == "Test Restore Agent" ]; then
    log "SUCCESS: Restore test passed - data recovered correctly"
    
    # Clean up test row
    docker compose -f "${COMPOSE_FILE}" exec -T postgres psql -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}" -c "DELETE FROM agents WHERE id = 'test-restore-001';"
    
    # Clean up test backup
    rm -f "${TEST_BACKUP_FILE}"
    
    log "Restore test completed successfully"
    exit 0
else
    log "ERROR: Restore test failed - data not recovered correctly"
    exit 1
fi