"""Tests for Marketing Activity and Evidence Registry API endpoints."""
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.models.content_item import ContentItemModel
from apps.models.base import Base
from datetime import datetime, timedelta, timezone

# Create test database
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

client = TestClient(app)


class TestMarketingActivityAPI:
    """Tests for Marketing Activity API endpoints."""
    
    def test_get_marketing_activity_unauthorized(self):
        """Test that marketing activity endpoint requires authentication."""
        response = client.get("/api/v1/marketing/activity")
        # Should return 401 when no Authorization header is supplied
        assert response.status_code == 401
    
    def test_get_marketing_activity_detail_unauthorized(self):
        """Test that marketing activity detail endpoint requires authentication."""
        response = client.get("/api/v1/marketing/activity/test-id")
        # Should return 401 when no Authorization header is supplied
        assert response.status_code == 401


class TestMarketingActivityModels:
    """Tests for Marketing Activity model changes."""
    
    def test_seo_metadata_persistence(self):
        """Test that SEO metadata fields are persisted correctly."""
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        session = TestingSessionLocal()
        
        content = ContentItemModel(
            title="SEO Article",
            channel="google",
            status="published",
            target_keyword="ai finance",
            search_intent="informational",
            meta_title="AI Finance Guide",
            meta_description="Learn about AI finance",
            canonical_url="https://example.com/seo-article",
            indexing_status="indexed",
            internal_links=["https://example.com/internal"]
        )
        session.add(content)
        session.commit()
        
        retrieved = session.query(ContentItemModel).filter(ContentItemModel.id == content.id).first()
        assert retrieved.target_keyword == "ai finance"
        assert retrieved.search_intent == "informational"
        assert retrieved.meta_title == "AI Finance Guide"
        assert retrieved.canonical_url == "https://example.com/seo-article"
        assert retrieved.indexing_status == "indexed"
        assert retrieved.internal_links == ["https://example.com/internal"]
        
        session.close()
    
    def test_analytics_metrics_persistence(self):
        """Test that analytics metrics are persisted correctly."""
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        session = TestingSessionLocal()
        
        content = ContentItemModel(
            title="Analytics Test",
            channel="x",
            status="published",
            impressions=1000,
            clicks=50,
            engagement=25,
            referrals=10,
            conversions=5,
            last_analytics_update=datetime.now(timezone.utc)
        )
        session.add(content)
        session.commit()
        
        retrieved = session.query(ContentItemModel).filter(ContentItemModel.id == content.id).first()
        assert retrieved.impressions == 1000
        assert retrieved.clicks == 50
        assert retrieved.engagement == 25
        assert retrieved.referrals == 10
        assert retrieved.conversions == 5
        assert retrieved.last_analytics_update is not None
        
        session.close()
    
    def test_approval_tracking_persistence(self):
        """Test that approval tracking fields are persisted correctly."""
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        session = TestingSessionLocal()
        
        content = ContentItemModel(
            title="Approved Content",
            channel="moltbook",
            status="approved",
            approved_at=datetime.now(timezone.utc) - timedelta(hours=1),
            approver="human_approver"
        )
        session.add(content)
        session.commit()
        
        retrieved = session.query(ContentItemModel).filter(ContentItemModel.id == content.id).first()
        assert retrieved.approved_at is not None
        assert retrieved.approver == "human_approver"
        
        session.close()
    
    def test_source_urls_persistence(self):
        """Test that source URLs are persisted correctly."""
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        session = TestingSessionLocal()
        
        content = ContentItemModel(
            title="Sourced Content",
            channel="moltbook",
            status="draft",
            source_urls=["https://example.com/source1", "https://example.com/source2"]
        )
        session.add(content)
        session.commit()
        
        retrieved = session.query(ContentItemModel).filter(ContentItemModel.id == content.id).first()
        assert retrieved.source_urls == ["https://example.com/source1", "https://example.com/source2"]
        
        session.close()
