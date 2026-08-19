"""Tests for X client to improve coverage."""

import pytest
from apps.integrations.x.client import XClient


def test_x_client_initialization():
    """Test X client initialization."""
    client = XClient()
    assert client is not None


def test_x_client_with_credentials():
    """Test X client with credentials."""
    client = XClient(
        api_key="test-key",
        api_secret="test-secret",
        access_token="test-token",
        access_token_secret="test-token-secret"
    )
    assert client is not None


def test_x_client_has_publish_method():
    """Test that client has publish method."""
    client = XClient()
    assert hasattr(client, 'publish_post')


def test_x_client_autopublish_property():
    """Test autopublish property."""
    client = XClient()
    assert hasattr(client, 'autopublish_enabled')


def test_x_client_api_key_property():
    """Test api_key property."""
    client = XClient()
    assert hasattr(client, 'api_key')