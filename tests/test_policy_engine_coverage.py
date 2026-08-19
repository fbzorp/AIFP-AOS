"""Comprehensive tests for policy engine to improve coverage."""

import pytest
from apps.core.policy.engine import PolicyEngine
from unittest.mock import Mock


def test_policy_engine_initialization():
    """Test PolicyEngine initialization."""
    engine = PolicyEngine()
    assert engine is not None


def test_policy_engine_validate_approval_with_mock():
    """Test validate_approval with mock session."""
    engine = PolicyEngine()
    mock_session = Mock()
    
    # Mock the query chain
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = None
    mock_session.query.return_value = mock_query
    
    result = engine.validate_approval(mock_session, "test-id", "test-hash")
    assert result is False  # Should return False when approval not found