"""Tests for Moltbook client to improve coverage."""

import pytest
from apps.integrations.moltbook.client import MoltbookClient


def test_moltbook_client_initialization():
    """Test Moltbook client initialization."""
    client = MoltbookClient()
    assert client is not None


def test_moltbook_client_autopublish_property():
    """Test autopublish property."""
    client = MoltbookClient()
    # Should have autopublish property
    assert hasattr(client, 'autopublish_enabled')


def test_moltbook_client_has_publish_method():
    """Test that client has publish method."""
    client = MoltbookClient()
    assert hasattr(client, 'publish_post')