"""Tests for audit event integrity and tamper resistance."""
import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from apps.api.config import Settings

from apps.models.base import Base
from apps.models.audit_event import AuditEventModel
from apps.core.audit.service import record_event, verify_audit_chain


class TestAuditIntegrityChain:
    """Tests for audit event hash chain integrity."""
    
    @pytest.fixture
    def db_session(self):
        """Create an in-memory SQLite database session for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
        session = TestingSessionLocal()
        try:
            yield session
            session.rollback()
        finally:
            session.close()
    
    def test_record_event_creates_hash(self, db_session):
        """Test that record_event creates proper hash for single event."""
        record_event(db_session, "TestAgent", "event1", "First event")
        db_session.flush()
        
        event = db_session.query(AuditEventModel).first()
        assert event.record_hash is not None
        assert len(event.record_hash) == 64
        assert event.prev_hash is None
    
    def test_multiple_events_get_hashes(self, db_session):
        """Test that multiple events all get proper hashes."""
        record_event(db_session, "TestAgent", "event1", "First event")
        db_session.flush()
        
        record_event(db_session, "TestAgent", "event2", "Second event", {"key": "value"})
        db_session.flush()
        
        record_event(db_session, "AnotherAgent", "event3", "Third event")
        db_session.flush()
        
        events = db_session.query(AuditEventModel).all()
        assert len(events) == 3
        for event in events:
            assert event.record_hash is not None
            assert len(event.record_hash) == 64
    
    def test_genesis_row_has_null_prev_hash(self, db_session):
        """Test that the first row (genesis) has NULL prev_hash."""
        record_event(db_session, "TestAgent", "genesis", "First event")
        db_session.commit()
        
        event = db_session.query(AuditEventModel).first()
        assert event.prev_hash is None
        assert event.record_hash is not None
    
    def test_tampering_detected(self, db_session):
        """Test that tampering with a row's message is detected via hash verification."""
        record_event(db_session, "TestAgent", "event1", "Original message")
        db_session.commit()
        
        record_event(db_session, "TestAgent", "event2", "Second message")
        db_session.commit()
        
        original_hash = db_session.query(AuditEventModel).first().record_hash
        
        event = db_session.query(AuditEventModel).first()
        event.message = "Tampered message"
        db_session.commit()
        
        tampered_event = db_session.query(AuditEventModel).first()
        assert tampered_event.message == "Tampered message"
        assert tampered_event.record_hash == original_hash
        
        from apps.core.audit.service import _compute_record_hash
        correct_hash = _compute_record_hash(
            prev_hash=tampered_event.prev_hash,
            id=tampered_event.id,
            agent_name=tampered_event.agent_name,
            event_type=tampered_event.event_type,
            message=tampered_event.message,
            metadata_json=tampered_event.metadata_json,
            created_at=tampered_event.created_at
        )
        
        assert tampered_event.record_hash != correct_hash
    
    def test_empty_chain_is_valid(self, db_session):
        """Test that an empty audit log is considered valid."""
        result = verify_audit_chain(db_session)
        
        assert result['valid'] is True
        assert result['total_records'] == 0
        assert result['broken_records'] == 0
    
    def test_metadata_included_in_hash(self, db_session):
        """Test that metadata is included in the hash computation."""
        metadata = {"user": "test", "action": "create"}
        record_event(db_session, "TestAgent", "event1", "Event with metadata", metadata)
        db_session.commit()
        
        event = db_session.query(AuditEventModel).first()
        original_hash = event.record_hash
        assert original_hash is not None
        
        event.metadata_json = {"user": "test", "action": "delete"}
        db_session.commit()
        
        tampered_hash = db_session.query(AuditEventModel).first().record_hash
        assert tampered_hash == original_hash
        
        from apps.core.audit.service import _compute_record_hash
        correct_hash = _compute_record_hash(
            prev_hash=event.prev_hash,
            id=event.id,
            agent_name=event.agent_name,
            event_type=event.event_type,
            message=event.message,
            metadata_json=event.metadata_json,
            created_at=event.created_at
        )
        
        assert tampered_hash != correct_hash


class TestPostgresTriggerProtection:
    """Tests for PostgreSQL trigger protection of audit events."""
    
    @pytest.fixture(scope="module")
    def postgres_engine(self):
        """Create a Postgres engine for integration tests."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url or not database_url.startswith("postgresql"):
            pytest.skip("PostgreSQL connection required for trigger tests")
        
        if database_url.startswith("postgresql+asyncpg"):
            database_url = database_url.replace("postgresql+asyncpg", "postgresql")
        
        engine = create_engine(database_url)
        Base.metadata.create_all(bind=engine)
        
        yield engine
        
        Base.metadata.drop_all(bind=engine)
    
    @pytest.fixture
    def postgres_session(self, postgres_engine):
        """Create a database session for each test with append-only trigger applied."""
        # Create the append-only trigger before yielding the session
        with postgres_engine.connect() as conn:
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION prevent_audit_modification()
                RETURNS TRIGGER AS $$
                BEGIN
                    RAISE EXCEPTION 'Audit events are append-only. Modification (UPDATE/DELETE) is not allowed.';
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;
            """))
            # Drop triggers if they exist to avoid duplicate errors
            conn.execute(text("DROP TRIGGER IF EXISTS audit_events_prevent_update ON audit_events"))
            conn.execute(text("DROP TRIGGER IF EXISTS audit_events_prevent_delete ON audit_events"))
            conn.execute(text("""
                CREATE TRIGGER audit_events_prevent_update
                BEFORE UPDATE ON audit_events
                FOR EACH ROW
                EXECUTE FUNCTION prevent_audit_modification();
            """))
            conn.execute(text("""
                CREATE TRIGGER audit_events_prevent_delete
                BEFORE DELETE ON audit_events
                FOR EACH ROW
                EXECUTE FUNCTION prevent_audit_modification();
            """))
            conn.commit()

        TestingSessionLocal = sessionmaker(bind=postgres_engine, expire_on_commit=False)
        session = TestingSessionLocal()
        try:
            yield session
            session.rollback()
        finally:
            session.close()
            # Clean up triggers
            with postgres_engine.connect() as conn:
                conn.execute(text("DROP TRIGGER IF EXISTS audit_events_prevent_update ON audit_events"))
                conn.execute(text("DROP TRIGGER IF EXISTS audit_events_prevent_delete ON audit_events"))
                conn.execute(text("DROP FUNCTION IF EXISTS prevent_audit_modification"))
                conn.commit()
    
    def test_update_prevented_by_trigger(self, postgres_session):
        """Test that UPDATE on audit_events is prevented by PostgreSQL trigger."""
        event = record_event(postgres_session, "TestAgent", "test", "Test message")
        postgres_session.commit()

        event.message = "Modified message"

        with pytest.raises(Exception) as exc_info:
            postgres_session.commit()

        assert "append-only" in str(exc_info.value).lower() or "modification" in str(exc_info.value).lower()
    
    def test_delete_prevented_by_trigger(self, postgres_session):
        """Test that DELETE on audit_events is prevented by PostgreSQL trigger."""
        event = record_event(postgres_session, "TestAgent", "test", "Test message")
        postgres_session.commit()

        postgres_session.delete(event)

        with pytest.raises(Exception) as exc_info:
            postgres_session.commit()

        assert "append-only" in str(exc_info.value).lower() or "modification" in str(exc_info.value).lower()
    
    def test_insert_still_works(self, postgres_session):
        """Test that INSERT operations still work with the trigger."""
        event = record_event(postgres_session, "TestAgent", "test", "Test message")
        postgres_session.commit()

        retrieved = postgres_session.query(AuditEventModel).first()
        assert retrieved is not None
        assert retrieved.message == "Test message"
        assert retrieved.record_hash is not None

    def test_record_event_with_populated_hash_succeeds(self, postgres_session):
        """Test that normal record_event call succeeds with populated record_hash under active trigger."""
        # This test proves the fix: record_event now computes hash before INSERT
        # avoiding the UPDATE that would trigger append-only protection
        event = record_event(postgres_session, "TestAgent", "event1", "Test event with hash")
        postgres_session.commit()

        # Verify the event was inserted successfully
        assert event is not None
        assert event.agent_name == "TestAgent"
        assert event.message == "Test event with hash"
        assert event.record_hash is not None
        assert len(event.record_hash) == 64

        # Verify the event can be retrieved
        retrieved = postgres_session.query(AuditEventModel).filter_by(id=event.id).first()
        assert retrieved is not None
        assert retrieved.record_hash == event.record_hash


class TestAsyncAuditRecording:
    """Tests for async audit recording functionality."""
    
    @pytest.mark.asyncio
    async def test_async_record_event_creates_hash(self):
        """Test that async record_event creates proper hash."""
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        from apps.core.audit.service import record_event_async
        from apps.models.base import Base
        
        async_db_url = "sqlite+aiosqlite:///:memory:"
        async_engine = create_async_engine(async_db_url)
        
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        AsyncSessionLocal = async_sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        async with AsyncSessionLocal() as session:
            await record_event_async(session, "TestAgent", "event1", "First event")
            await session.commit()
            
            result = await session.execute(
                text("SELECT id, record_hash, prev_hash FROM audit_events")
            )
            event = result.fetchone()
            
            assert event is not None
            assert event[1] is not None
            assert len(event[1]) == 64
            assert event[2] is None
        
        await async_engine.dispose()


class TestProductionValidation:
    """Tests for production configuration validation."""

    def test_production_validation_detects_default_secret_key(self):
        """Test that production validation detects default SECRET_KEY."""
        settings = Settings(
            APP_ENV='production',
            SECRET_KEY='dev-secret-key-change-in-production',
            DEEPSEEK_API_KEY='test-key',
            DATABASE_URL='postgresql+asyncpg://aifp:realpassword@localhost:5432/aifp_prod',
            MOLTBOOK_AUTOPUBLISH=False,
            FOUNDER_CONTENT_MOLTBOOK_AUTOPUBLISH=False,
            TECHNICAL_CONTENT_MOLTBOOK_AUTOPUBLISH=False,
            SEO_CONTENT_MOLTBOOK_AUTOPUBLISH=False
        )
        errors = settings.validate_production_startup()
        assert len(errors) == 1
        assert 'SECRET_KEY must be set to a non-default value in production' in errors[0]

    def test_production_validation_detects_missing_deepseek_key(self):
        """Test that production validation detects missing DEEPSEEK_API_KEY."""
        settings = Settings(
            APP_ENV='production',
            SECRET_KEY='real-secret-key',
            DEEPSEEK_API_KEY=None,
            DATABASE_URL='postgresql+asyncpg://aifp:realpassword@localhost:5432/aifp_prod',
            MOLTBOOK_AUTOPUBLISH=False,
            FOUNDER_CONTENT_MOLTBOOK_AUTOPUBLISH=False,
            TECHNICAL_CONTENT_MOLTBOOK_AUTOPUBLISH=False,
            SEO_CONTENT_MOLTBOOK_AUTOPUBLISH=False
        )
        errors = settings.validate_production_startup()
        assert len(errors) == 1
        assert 'DEEPSEEK_API_KEY is required in production' in errors[0]

    def test_production_validation_detects_default_database_password(self):
        """Test that production validation detects default database password."""
        settings = Settings(
            APP_ENV='production',
            SECRET_KEY='real-secret-key',
            DEEPSEEK_API_KEY='test-key',
            DATABASE_URL='postgresql+asyncpg://aifp:prod_password@localhost:5432/aifp_prod',
            MOLTBOOK_AUTOPUBLISH=False,
            FOUNDER_CONTENT_MOLTBOOK_AUTOPUBLISH=False,
            TECHNICAL_CONTENT_MOLTBOOK_AUTOPUBLISH=False,
            SEO_CONTENT_MOLTBOOK_AUTOPUBLISH=False
        )
        errors = settings.validate_production_startup()
        assert len(errors) == 1
        assert "Database password must not be the default 'prod_password' in production" in errors[0]

    def test_production_validation_passes_with_valid_config(self):
        """Test that production validation passes with valid configuration."""
        settings = Settings(
            APP_ENV='production',
            SECRET_KEY='real-secret-key',
            DEEPSEEK_API_KEY='test-key',
            DATABASE_URL='postgresql+asyncpg://aifp:realpassword@localhost:5432/aifp_prod',
            MOLTBOOK_AUTOPUBLISH=False,
            FOUNDER_CONTENT_MOLTBOOK_AUTOPUBLISH=False,
            TECHNICAL_CONTENT_MOLTBOOK_AUTOPUBLISH=False,
            SEO_CONTENT_MOLTBOOK_AUTOPUBLISH=False
        )
        errors = settings.validate_production_startup()
        assert len(errors) == 0

    def test_development_environment_always_passes_validation(self):
        """Test that development environment always passes validation."""
        settings = Settings(
            APP_ENV='development',
            SECRET_KEY='dev-secret-key-change-in-production',
            DEEPSEEK_API_KEY=None,
            DATABASE_URL='postgresql+asyncpg://aifp:devpassword@localhost:5432/aifp_dev'
        )
        errors = settings.validate_production_startup()
        assert len(errors) == 0