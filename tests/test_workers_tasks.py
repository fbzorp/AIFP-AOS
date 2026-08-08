"""
Tests for apps.workers.tasks module.
Tests the task runner, content routing, and publishing logic.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock, Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.models.base import Base, get_sync_session
from apps.models.task import TaskModel
from apps.models.content_item import ContentItemModel
from apps.models.audit_event import AuditEventModel
from apps.workers.tasks import run_agent_task, publish_content, _perform_publish_logic

# Setup in-memory SQLite for testing
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create and clean up test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_session():
    """Create a test session."""
    return TestingSessionLocal()


class TestRunAgentTask:
    """Tests for the run_agent_task function."""

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.get_agent")
    @patch("apps.workers.tasks.record_event")
    def test_run_agent_task_not_found(self, mock_record, mock_get_agent, mock_get_session):
        """Test that task returns early if task not found."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        # Run with non-existent task ID
        run_agent_task("non-existent-id")
        
        # Verify record_event was not called since task doesn't exist
        mock_record.assert_not_called()

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.get_agent")
    @patch("apps.workers.tasks.record_event")
    def test_run_agent_task_already_succeeded(self, mock_record, mock_get_agent, mock_get_session):
        """Test that task skips if already succeeded (idempotency)."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        # Create a task that already succeeded
        task = TaskModel(
            id="task-123",
            task_type="Content Strategy",
            status="succeeded",
            input_data={},
            result={"outcome": "success"}
        )
        session.add(task)
        session.commit()
        
        run_agent_task("task-123")
        
        # Verify task status unchanged
        assert session.query(TaskModel).first().status == "succeeded"

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.get_agent")
    @patch("apps.workers.tasks.record_event")
    def test_run_agent_task_agent_not_found(self, mock_record, mock_get_agent, mock_get_session):
        """Test that task fails gracefully when agent is not found."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        # Mock get_agent to return None
        mock_get_agent.return_value = None
        
        # Create a pending task
        task = TaskModel(
            id="task-123",
            task_type="Unknown Agent",
            status="pending",
            input_data={}
        )
        session.add(task)
        session.commit()
        
        # Run task - should fail
        with pytest.raises(ValueError, match="Agent for Unknown Agent not found"):
            run_agent_task("task-123")
        
        # Verify task status is failed
        task = session.query(TaskModel).filter(TaskModel.id == "task-123").first()
        assert task.status == "failed"
        assert "Agent for Unknown Agent not found" in task.error

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.get_agent")
    @patch("apps.workers.tasks.record_event")
    def test_run_agent_task_success_simple(self, mock_record, mock_get_agent, mock_get_session):
        """Test successful task execution without follow-on tasks."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.name = "Test Agent"
        mock_agent.execute = AsyncMock(return_value={"outcome": "completed"})
        mock_get_agent.return_value = mock_agent
        
        # Create a simple task
        task = TaskModel(
            id="task-123",
            task_type="Test Agent",
            status="pending",
            input_data={"test": "data"}
        )
        session.add(task)
        session.commit()
        
        run_agent_task("task-123")
        
        # Verify task succeeded
        task = session.query(TaskModel).filter(TaskModel.id == "task-123").first()
        assert task.status == "succeeded"
        assert task.result == {"outcome": "completed"}
        
        # Verify events recorded
        assert mock_record.call_count >= 2  # task_started and task_succeeded

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.get_agent")
    @patch("apps.workers.tasks.record_event")
    def test_run_agent_task_exception_handling(self, mock_record, mock_get_agent, mock_get_session):
        """Test that task exceptions are properly recorded and re-raised."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        # Mock agent that raises exception
        mock_agent = Mock()
        mock_agent.name = "Test Agent"
        mock_agent.execute = AsyncMock(side_effect=ValueError("Test error"))
        mock_get_agent.return_value = mock_agent
        
        # Create a task
        task = TaskModel(
            id="task-123",
            task_type="Test Agent",
            status="pending",
            input_data={}
        )
        session.add(task)
        session.commit()
        
        # Run task - should raise
        with pytest.raises(ValueError, match="Test error"):
            run_agent_task("task-123")
        
        # Verify task status is failed
        task = session.query(TaskModel).filter(TaskModel.id == "task-123").first()
        assert task.status == "failed"
        assert "Test error" in task.error
        
        # Verify failure event recorded
        calls = [call for call in mock_record.call_args_list if "task_failed" in str(call)]
        assert len(calls) > 0


class TestContentRoutingStrategy:
    """Tests for content routing logic in run_agent_task."""

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.get_agent")
    @patch("apps.workers.tasks.record_event")
    def test_content_routing_to_seo_agent_by_channel(self, mock_record, mock_get_agent, mock_get_session):
        """Test routing to SEO Content agent based on 'google' channel keyword."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.name = "Content Strategy"
        mock_agent.execute = AsyncMock(return_value={
            "outcome": "weekly_plan_created",
            "items": ["item-1"]
        })
        mock_get_agent.return_value = mock_agent
        
        # Create content item with SEO channel
        item = ContentItemModel(
            id="item-1",
            channel="google",  # SEO keyword
            format="article",
            objective="increase visibility"
        )
        session.add(item)
        
        # Create Content Strategy task
        task = TaskModel(
            id="task-123",
            task_type="Content Strategy",
            status="pending",
            input_data={}
        )
        session.add(task)
        session.commit()
        
        run_agent_task("task-123")
        
        # Verify follow-on task created for SEO Content
        follow_on = session.query(TaskModel).filter(
            TaskModel.task_type == "SEO Content",
            TaskModel.status == "pending"
        ).first()
        assert follow_on is not None
        assert follow_on.input_data == {"content_item_id": "item-1"}

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.get_agent")
    @patch("apps.workers.tasks.record_event")
    def test_content_routing_to_seo_agent_by_format(self, mock_record, mock_get_agent, mock_get_session):
        """Test routing to SEO Content agent based on 'blog' format keyword."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        mock_agent = Mock()
        mock_agent.name = "Content Strategy"
        mock_agent.execute = AsyncMock(return_value={
            "outcome": "weekly_plan_created",
            "items": ["item-1"]
        })
        mock_get_agent.return_value = mock_agent
        
        # Create content item with SEO format
        item = ContentItemModel(
            id="item-1",
            channel="twitter",
            format="blog",  # SEO keyword
            objective="share updates"
        )
        session.add(item)
        
        task = TaskModel(
            id="task-123",
            task_type="Content Strategy",
            status="pending",
            input_data={}
        )
        session.add(task)
        session.commit()
        
        run_agent_task("task-123")
        
        follow_on = session.query(TaskModel).filter(
            TaskModel.task_type == "SEO Content"
        ).first()
        assert follow_on is not None

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.get_agent")
    @patch("apps.workers.tasks.record_event")
    def test_content_routing_to_technical_agent(self, mock_record, mock_get_agent, mock_get_session):
        """Test routing to Technical Content agent based on technical keywords."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        mock_agent = Mock()
        mock_agent.name = "Content Strategy"
        mock_agent.execute = AsyncMock(return_value={
            "outcome": "weekly_plan_created",
            "items": ["item-1"]
        })
        mock_get_agent.return_value = mock_agent
        
        # Create content item with technical format
        item = ContentItemModel(
            id="item-1",
            channel="discord",
            format="tutorial",  # Technical keyword
            objective="educate developers"
        )
        session.add(item)
        
        task = TaskModel(
            id="task-123",
            task_type="Content Strategy",
            status="pending",
            input_data={}
        )
        session.add(task)
        session.commit()
        
        run_agent_task("task-123")
        
        follow_on = session.query(TaskModel).filter(
            TaskModel.task_type == "Technical Content"
        ).first()
        assert follow_on is not None

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.get_agent")
    @patch("apps.workers.tasks.record_event")
    def test_content_routing_to_technical_agent_by_objective(self, mock_record, mock_get_agent, mock_get_session):
        """Test routing to Technical Content based on SDK/code keywords in objective."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        mock_agent = Mock()
        mock_agent.name = "Content Strategy"
        mock_agent.execute = AsyncMock(return_value={
            "outcome": "weekly_plan_created",
            "items": ["item-1"]
        })
        mock_get_agent.return_value = mock_agent
        
        # Create content item with SDK keyword in objective
        item = ContentItemModel(
            id="item-1",
            channel="twitter",
            format="post",
            objective="SDK integration guide"  # Technical keyword
        )
        session.add(item)
        
        task = TaskModel(
            id="task-123",
            task_type="Content Strategy",
            status="pending",
            input_data={}
        )
        session.add(task)
        session.commit()
        
        run_agent_task("task-123")
        
        follow_on = session.query(TaskModel).filter(
            TaskModel.task_type == "Technical Content"
        ).first()
        assert follow_on is not None

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.get_agent")
    @patch("apps.workers.tasks.record_event")
    def test_content_routing_to_founder_agent(self, mock_record, mock_get_agent, mock_get_session):
        """Test routing to Founder Content agent as default."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        mock_agent = Mock()
        mock_agent.name = "Content Strategy"
        mock_agent.execute = AsyncMock(return_value={
            "outcome": "weekly_plan_created",
            "items": ["item-1"]
        })
        mock_get_agent.return_value = mock_agent
        
        # Create generic content item
        item = ContentItemModel(
            id="item-1",
            channel="newsletter",
            format="email",
            objective="weekly update"
        )
        session.add(item)
        
        task = TaskModel(
            id="task-123",
            task_type="Content Strategy",
            status="pending",
            input_data={}
        )
        session.add(task)
        session.commit()
        
        run_agent_task("task-123")
        
        # Should route to Founder Content (default)
        follow_on = session.query(TaskModel).filter(
            TaskModel.task_type == "Founder Content"
        ).first()
        assert follow_on is not None

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.get_agent")
    @patch("apps.workers.tasks.record_event")
    def test_content_routing_missing_item(self, mock_record, mock_get_agent, mock_get_session):
        """Test that routing skips missing content items."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        mock_agent = Mock()
        mock_agent.name = "Content Strategy"
        mock_agent.execute = AsyncMock(return_value={
            "outcome": "weekly_plan_created",
            "items": ["missing-item-id"]
        })
        mock_get_agent.return_value = mock_agent
        
        task = TaskModel(
            id="task-123",
            task_type="Content Strategy",
            status="pending",
            input_data={}
        )
        session.add(task)
        session.commit()
        
        run_agent_task("task-123")
        
        # Verify no follow-on tasks created
        follow_ons = session.query(TaskModel).filter(TaskModel.id != "task-123").all()
        assert len(follow_ons) == 0


class TestFollowOnTaskChaining:
    """Tests for follow-on task enqueuing in content agents."""

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.get_agent")
    @patch("apps.workers.tasks.record_event")
    def test_follow_on_task_from_technical_content(self, mock_record, mock_get_agent, mock_get_session):
        """Test that Technical Content generates Compliance & Brand follow-on task."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        mock_agent = Mock()
        mock_agent.name = "Technical Content"
        mock_agent.execute = AsyncMock(return_value={
            "outcome": "tutorial_generated",
            "item_id": "item-1"
        })
        mock_get_agent.return_value = mock_agent
        
        task = TaskModel(
            id="task-123",
            task_type="Technical Content",
            status="pending",
            input_data={"content_item_id": "item-1"}
        )
        session.add(task)
        session.commit()
        
        run_agent_task("task-123")
        
        # Verify follow-on task created
        follow_on = session.query(TaskModel).filter(
            TaskModel.task_type == "Compliance & Brand"
        ).first()
        assert follow_on is not None
        assert follow_on.status == "pending"
        assert follow_on.input_data == {"content_item_id": "item-1"}

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.get_agent")
    @patch("apps.workers.tasks.record_event")
    def test_follow_on_task_from_founder_content(self, mock_record, mock_get_agent, mock_get_session):
        """Test that Founder Content generates Compliance & Brand follow-on task."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        mock_agent = Mock()
        mock_agent.name = "Founder Content"
        mock_agent.execute = AsyncMock(return_value={
            "outcome": "founder_draft_ready",
            "item_id": "item-1"
        })
        mock_get_agent.return_value = mock_agent
        
        task = TaskModel(
            id="task-123",
            task_type="Founder Content",
            status="pending",
            input_data={"content_item_id": "item-1"}
        )
        session.add(task)
        session.commit()
        
        run_agent_task("task-123")
        
        follow_on = session.query(TaskModel).filter(
            TaskModel.task_type == "Compliance & Brand"
        ).first()
        assert follow_on is not None

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.get_agent")
    @patch("apps.workers.tasks.record_event")
    def test_follow_on_task_from_seo_content(self, mock_record, mock_get_agent, mock_get_session):
        """Test that SEO Content generates Compliance & Brand follow-on task."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        mock_agent = Mock()
        mock_agent.name = "SEO Content"
        mock_agent.execute = AsyncMock(return_value={
            "outcome": "seo_content_generated",
            "item_id": "item-1"
        })
        mock_get_agent.return_value = mock_agent
        
        task = TaskModel(
            id="task-123",
            task_type="SEO Content",
            status="pending",
            input_data={"content_item_id": "item-1"}
        )
        session.add(task)
        session.commit()
        
        run_agent_task("task-123")
        
        follow_on = session.query(TaskModel).filter(
            TaskModel.task_type == "Compliance & Brand"
        ).first()
        assert follow_on is not None

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.get_agent")
    @patch("apps.workers.tasks.record_event")
    def test_follow_on_task_not_created_for_wrong_outcome(self, mock_record, mock_get_agent, mock_get_session):
        """Test that follow-on task is not created if outcome doesn't match."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        mock_agent = Mock()
        mock_agent.name = "Technical Content"
        mock_agent.execute = AsyncMock(return_value={
            "outcome": "unexpected_outcome",
            "item_id": "item-1"
        })
        mock_get_agent.return_value = mock_agent
        
        task = TaskModel(
            id="task-123",
            task_type="Technical Content",
            status="pending",
            input_data={"content_item_id": "item-1"}
        )
        session.add(task)
        session.commit()
        
        run_agent_task("task-123")
        
        # Verify no follow-on task created
        follow_ons = session.query(TaskModel).filter(TaskModel.id != "task-123").all()
        assert len(follow_ons) == 0


class TestPublishingLogic:
    """Tests for the _perform_publish_logic and publish_content functions."""

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.PolicyEngine")
    @patch("apps.integrations.moltbook.client.MoltbookClient")
    def test_publish_content_success(self, mock_client_class, mock_policy, mock_get_session):
        """Test successful content publication."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        # Mock policy
        mock_policy.return_value.validate_approval.return_value = True
        
        # Mock moltbook client
        mock_client = AsyncMock()
        mock_client.publish_post = AsyncMock(return_value={
            "post_id": "post-123",
            "post_url": "https://moltbook.com/posts/post-123",
            "dry_run": False
        })
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Create content
        content = ContentItemModel(
            id="content-1",
            title="Test Post",
            body="Test body",
            channel="general",
            status="approved"
        )
        session.add(content)
        session.commit()
        
        with patch("apps.api.config.settings.MOLTBOOK_ALLOWED_SUBMOLTS", "general"):
            publish_content("content-1", "appr-123", "hash-123")
        
        # Verify content updated
        content = session.query(ContentItemModel).first()
        assert content.status == "published"
        assert content.post_id == "post-123"

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.PolicyEngine")
    def test_publish_denied_invalid_approval(self, mock_policy, mock_get_session):
        """Test that publish is denied for invalid approval."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        # Mock policy to reject approval
        mock_policy.return_value.validate_approval.return_value = False
        
        content = ContentItemModel(
            id="content-1",
            title="Test Post",
            channel="general",
            status="approved"
        )
        session.add(content)
        session.commit()
        
        with pytest.raises(ValueError, match="Invalid approval"):
            publish_content("content-1", "bad-appr", "bad-hash")

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.PolicyEngine")
    def test_publish_denied_unapproved_status(self, mock_policy, mock_get_session):
        """Test that publish is denied if content is not approved."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        content = ContentItemModel(
            id="content-1",
            title="Test Post",
            channel="general",
            status="draft"  # Not approved
        )
        session.add(content)
        session.commit()
        
        with pytest.raises(ValueError, match="must be approved"):
            publish_content("content-1", "appr-123", "hash-123")

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.PolicyEngine")
    def test_publish_denied_content_not_found(self, mock_policy, mock_get_session):
        """Test that publish is denied if content not found."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        mock_policy.return_value.validate_approval.return_value = True
        
        with pytest.raises(ValueError, match="Content not found"):
            publish_content("missing-id", "appr-123", "hash-123")

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.PolicyEngine")
    def test_publish_denied_not_in_allowlist(self, mock_policy, mock_get_session):
        """Test that publish is denied if submolt not in allowlist."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        mock_policy.return_value.validate_approval.return_value = True
        
        content = ContentItemModel(
            id="content-1",
            title="Test Post",
            channel="forbidden-channel",
            status="approved"
        )
        session.add(content)
        session.commit()
        
        with patch("apps.api.config.settings.MOLTBOOK_ALLOWED_SUBMOLTS", "general,aifintech"):
            with pytest.raises(ValueError, match="not in allowlist"):
                publish_content("content-1", "appr-123", "hash-123")

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.PolicyEngine")
    @patch("apps.integrations.moltbook.client.MoltbookClient")
    def test_publish_idempotency_already_published(self, mock_client_class, mock_policy, mock_get_session):
        """Test that publish is idempotent (already published content)."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        mock_policy.return_value.validate_approval.return_value = True
        
        # Create already-published content
        content = ContentItemModel(
            id="content-1",
            title="Test Post",
            channel="general",
            status="published",
            post_id="existing-post-id",
            post_url="https://moltbook.com/posts/existing-post-id"
        )
        session.add(content)
        session.commit()
        
        result = publish_content("content-1", "appr-123", "hash-123")
        
        # Verify idempotent response
        assert result["status"] == "already_published"
        assert result["post_id"] == "existing-post-id"
        
        # Verify client was not called
        mock_client_class.assert_not_called()

    @patch("apps.workers.tasks.get_sync_session")
    @patch("apps.workers.tasks.PolicyEngine")
    @patch("apps.integrations.moltbook.client.MoltbookClient")
    def test_publish_with_variants(self, mock_client_class, mock_policy, mock_get_session):
        """Test publishing content with variants as body fallback."""
        session = TestingSessionLocal()
        mock_get_session.return_value.__enter__.return_value = session
        
        mock_policy.return_value.validate_approval.return_value = True
        
        mock_client = AsyncMock()
        mock_client.publish_post = AsyncMock(return_value={
            "post_id": "post-123",
            "post_url": "https://moltbook.com/posts/post-123",
            "dry_run": False
        })
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Create content without body but with variants
        content = ContentItemModel(
            id="content-1",
            title="Test Post",
            body=None,  # No body
            variants=["variant1", "variant2"],
            channel="general",
            status="approved"
        )
        session.add(content)
        session.commit()
        
        with patch("apps.api.config.settings.MOLTBOOK_ALLOWED_SUBMOLTS", "general"):
            publish_content("content-1", "appr-123", "hash-123")
        
        # Verify client was called with variants as body
        assert mock_client.publish_post.called
        call_kwargs = mock_client.publish_post.call_args.kwargs
        assert call_kwargs["body"] == str(["variant1", "variant2"])
