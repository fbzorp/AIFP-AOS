# Audit Integrity Documentation

## Overview

The audit log system is designed to be tamper-resistant using cryptographic hash chaining and database-level protections.

## Hash Chain Architecture

### Integrity Fields

Each audit event record contains two integrity fields:

- `prev_hash`: The SHA256 hash of the previous record's `record_hash` (NULL for the genesis row)
- `record_hash`: The SHA256 hash computed from all record fields plus the previous hash

### Hash Computation

```
record_hash = sha256(
    prev_hash + 
    id + 
    agent_name + 
    event_type + 
    message + 
    canonical_json(metadata_json) + 
    created_at_iso
)
```

### Chain Properties

- **Deterministic**: The same input always produces the same hash
- **Append-only**: New records reference the previous record's hash
- **Tamper-evident**: Any modification to a record breaks the chain
- **Order-dependent**: Records are processed in `created_at, id` order

## Database-Level Protection

### PostgreSQL Triggers

The system uses PostgreSQL triggers to enforce append-only behavior:

```sql
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit events are append-only. Modification (UPDATE/DELETE) is not allowed.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_events_prevent_update
BEFORE UPDATE ON audit_events
FOR EACH ROW
EXECUTE FUNCTION prevent_audit_modification();

CREATE TRIGGER audit_events_prevent_delete
BEFORE DELETE ON audit_events
FOR EACH ROW
EXECUTE FUNCTION prevent_audit_modification();
```

### Role-Based Access Control

For enhanced security, implement role separation:

#### Application Role (Least Privilege)

```sql
-- Create application role with limited permissions
CREATE ROLE aifp_app WITH LOGIN PASSWORD 'secure_password';

-- Grant only INSERT and SELECT on audit_events
GRANT INSERT, SELECT ON audit_events TO aifp_app;

-- Grant SELECT on other tables as needed
GRANT SELECT ON content_items TO aifp_app;
GRANT SELECT ON sources TO aifp_app;
-- ... other table grants
```

#### Administrative Role (Maintenance)

```sql
-- Create admin role for maintenance operations
CREATE ROLE aifp_admin WITH LOGIN PASSWORD 'very_secure_password';

-- Grant full permissions for maintenance
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aifp_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aifp_admin;

-- Allow admin to modify audit events for maintenance
GRANT UPDATE, DELETE ON audit_events TO aifp_admin;
```

#### Application Configuration

Update your application configuration to use the application role:

```python
# In .env or config
DATABASE_URL=postgresql://aifp_app:secure_password@localhost:5432/aifp_dev
```

#### Maintenance Operations

For audit log maintenance (e.g., archival, cleanup), use the admin role:

```bash
# Connect as admin for maintenance
psql -U aifp_admin -d aifp_dev

-- Disable triggers temporarily for maintenance
ALTER TABLE audit_events DISABLE TRIGGER audit_events_prevent_update;
ALTER TABLE audit_events DISABLE TRIGGER audit_events_prevent_delete;

-- Perform maintenance operations
DELETE FROM audit_events WHERE created_at < '2024-01-01';

-- Re-enable triggers
ALTER TABLE audit_events ENABLE TRIGGER audit_events_prevent_update;
ALTER TABLE audit_events ENABLE TRIGGER audit_events_prevent_delete;
```

## Verification

### Running Integrity Check

Use the provided verification script:

```bash
python scripts/verify_audit_integrity.py
```

### Programmatic Verification

```python
from apps.core.audit.service import verify_audit_chain
from apps.models.base import get_sync_session

with get_sync_session() as session:
    result = verify_audit_chain(session)
    
    if result['valid']:
        print("Audit chain is valid")
    else:
        print(f"Chain broken at record: {result['first_broken_id']}")
```

### Verification Output

The verification function returns:

```python
{
    'valid': bool,           # True if chain is intact
    'first_broken_id': str,  # ID of first broken record (None if valid)
    'total_records': int,    # Total number of records checked
    'broken_records': int,   # Number of broken records found
    'error': str (optional)  # Error message if verification failed
}
```

## Assumptions and Limitations

### Single-Writer Assumption

The hash chaining assumes a single-writer model for audit events. Concurrent inserts could potentially cause race conditions. In production:

- Ensure audit writes are serialized
- Use application-level locking if concurrent writes are necessary
- Consider using database transactions with proper isolation levels

### SQLite Compatibility

The trigger protection is PostgreSQL-specific. SQLite databases:

- Do not have trigger protection (UPDATE/DELETE still possible)
- Still benefit from hash chain integrity verification
- Should use additional application-level checks

### Async Session Handling

The `record_event()` function has limitations with async sessions:

- For async contexts, use `record_event_async()` instead
- The sync version cannot properly await database operations in async sessions
- Hash computation may be incomplete for sync calls on async sessions

## Migration

The integrity system is added via Alembic migration `20260811_add_audit_integrity`:

- Adds `prev_hash` and `record_hash` columns
- Backfills existing records with proper hash chain
- Creates PostgreSQL triggers for append-only enforcement
- Maintains single linear migration chain

## Security Considerations

1. **Credential Rotation**: If audit logs are exposed, rotate database credentials
2. **Hash Algorithm**: SHA256 is used; consider upgrading to SHA3 in the future
3. **Key Management**: Protect admin role credentials with proper secrets management
4. **Monitoring**: Monitor for trigger violations (attempted modifications)
5. **Backup**: Regular backups of audit logs with hash verification

## Troubleshooting

### Chain Break Detection

If verification fails:

1. Identify the broken record using `first_broken_id`
2. Check for manual modifications or database corruption
3. Verify trigger protection is active on PostgreSQL
4. Review application logs for unusual database operations

### Trigger Errors

If INSERT operations fail with trigger errors:

1. Verify the trigger function exists: `SELECT * FROM pg_trigger WHERE tgname LIKE 'audit_events%'`
2. Check for conflicting triggers
3. Ensure you're not using the admin role for normal operations
4. Check for existing columns that might conflict

### Migration Issues

If migration fails:

1. Check PostgreSQL version (triggers require PostgreSQL)
2. Verify database user has CREATE TRIGGER permissions
3. Check for existing columns that might conflict
4. Review migration logs for specific error messages