"""Test for MCP client to improve coverage."""

import pytest
from apps.integrations.mcp.client import MCPClient


def test_mcp_client_init():
    """Test MCPClient initialization."""
    client = MCPClient("test_url")
    assert client is not None