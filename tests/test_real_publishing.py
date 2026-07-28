
import pytest
import respx
from httpx import Response
from sqlalchemy.sql import func
from datetime import datetime, timezone
from apps.api.config import settings
from apps.models.content_item import ContentItemModel
from apps.models.approval import ApprovalModel
from apps.core.policy.engine import compute_draft_hash
from apps.workers.tasks import _perform_publish_logic
from apps.models.base import get_sync_session

@pytest.mark.asyncio
async def test_real_publish_flow_non_dry_run():
    # 2. Patch settings to enable autopublish
    original_autopublish = settings.MOLTBOOK_AUTOPUBLISH
    original_base_url = settings.MOLTBOOK_BASE_URL
    settings.MOLTBOOK_AUTOPUBLISH = True
    settings.MOLTBOOK_BASE_URL = "https://www.moltbook.com"

    # 1. Setup respx mock for Moltbook API
    with respx.mock(base_url="https://www.moltbook.com") as respx_mock:
        # Mock the POST /api/v1/posts endpoint
        respx_mock.post("/api/v1/posts").mock(return_value=Response(
            201, 
            json={
                "success": True,
                "post": {
                    "id": "real-post-123"
                }
            }
        ))
        
        try:
            with get_sync_session() as session:
                # 3. Create test content
                content = ContentItemModel(
                    title="Test Real Publication",
                    channel="aifintech",
                    body="Test body",
                    status="draft"
                )
                session.add(content)
                session.flush()
                content_id = content.id
                
                # 4. Create approval
                draft_hash = compute_draft_hash(content)
                approval = ApprovalModel(
                    content_id=content_id,
                    draft_hash=draft_hash,
                    status="approved"
                )
                session.add(approval)
                session.flush()
                approval_id = approval.id
                
                content.status = "approved"
                session.commit()
            
            # 5. Run publish logic
            with get_sync_session() as session:
                result = await _perform_publish_logic(session, content_id, approval_id, draft_hash)
            
            # 6. Assertions
            assert result["status"] == "published"
            assert result["post_id"] == "real-post-123"
            assert result["post_url"] == "https://www.moltbook.com/posts/real-post-123"
            assert result["dry_run"] is False
            
            # Verify database persistence
            with get_sync_session() as session:
                updated_content = session.query(ContentItemModel).filter(ContentItemModel.id == content_id).first()
                assert updated_content.status == "published"
                assert updated_content.post_id == "real-post-123"
                assert updated_content.post_url == "https://www.moltbook.com/posts/real-post-123"
                assert updated_content.published_at is not None
                
                # Check audit event
                from apps.models.audit_event import AuditEventModel
                audit = session.query(AuditEventModel).filter(
                    AuditEventModel.event_type == "content_published",
                    AuditEventModel.agent_name == "System"
                ).order_by(AuditEventModel.created_at.desc()).first()
                assert audit is not None
                assert audit.metadata_json.get("dry_run") is False
                assert audit.metadata_json.get("post_id") == "real-post-123"
                
        finally:
            settings.MOLTBOOK_AUTOPUBLISH = original_autopublish
            settings.MOLTBOOK_BASE_URL = original_base_url
