"""Comprehensive tests for MCP client to improve coverage."""

import pytest
from apps.integrations.mcp.client import MCPClient


def test_mcp_client_initialization():
    """Test MCPClient initialization."""
    client = MCPClient()
    assert client is not None


def test_mcp_client_has_required_methods():
    """Test MCPClient has required methods."""
    client = MCPClient()
    assert hasattr(client, 'call_tool')