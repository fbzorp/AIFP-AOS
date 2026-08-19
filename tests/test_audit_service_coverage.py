"""Tests for audit service to improve coverage."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from apps.core.audit.service import record_event, record_event_async


@pytest.mark.asyncio
async def test_record_event_async_basic():
    """Test basic async event recording."""
    mock_session = Mock()
    mock_session.add = Mock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    await record_event_async(
        mock_session,
        agent_name="test_agent",
        event_type="test_event",
        message="Test message",
        metadata={"key": "value"}
    )
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_record_event_async_with_metadata():
    """Test async event recording with complex metadata."""
    mock_session = Mock()
    mock_session.add = Mock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    complex_metadata = {
        "nested": {"key": "value"},
        "list": [1, 2, 3],
        "number": 42
    }
    
    await record_event_async(
        mock_session,
        agent_name="test_agent",
        event_type="test_event",
        message="Test with complex metadata",
        metadata=complex_metadata
    )
    
    mock_session.add.assert_called_once()


def test_record_event_sync():
    """Test synchronous event recording."""
    mock_session = Mock()
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.refresh = Mock()
    
    record_event(
        mock_session,
        agent_name="test_agent",
        event_type="test_event",
        message="Test sync event",
        metadata={"key": "value"}
    )
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()