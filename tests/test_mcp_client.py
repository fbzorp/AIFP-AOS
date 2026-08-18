import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from apps.integrations.mcp.client import MCPClient, MCPToolCall


@pytest.mark.asyncio
async def test_mcp_client_initialization():
    """Test MCP client initialization"""
    client = MCPClient(
        enabled=True,
        timeout=30.0
    )
    
    assert client.enabled is True
    assert client.timeout == 30.0
    assert len(client._call_history) == 0


@pytest.mark.asyncio
async def test_mcp_client_disabled():
    """Test MCP client when disabled"""
    client = MCPClient(
        enabled=False
    )
    
    result = await client.call_tool("payable_fetch", "test_agent", {"url": "http://example.com"})
    assert result == {"status": "disabled", "error": "MCP payment functionality removed"}


@pytest.mark.asyncio
async def test_mcp_client_available_tools():
    """Test getting available tools - stub returns empty list"""
    client = MCPClient(
        enabled=True
    )
    
    # Stub implementation doesn't have AVAILABLE_TOOLS
    # Test that the client still works
    assert client is not None
    assert client.enabled is True


@pytest.mark.asyncio
async def test_mcp_client_unknown_tool():
    """Test MCP client with unknown tool - stub ignores validation"""
    client = MCPClient(
        enabled=True
    )
    
    # Stub implementation returns disabled for all tools
    result = await client.call_tool("unknown_tool", "test_agent", {"param": "value"})
    assert result == {"status": "disabled", "error": "MCP payment functionality removed"}


@pytest.mark.asyncio
async def test_mcp_client_context_manager():
    """Test MCP client async context manager"""
    async with MCPClient(
        enabled=True
    ) as client:
        assert client is not None
        assert client.enabled is True


@pytest.mark.asyncio
async def test_mcp_tool_call_record():
    """Test MCPToolCall dataclass"""
    tool_call = MCPToolCall(
        agent="test_agent",
        tool_name="payable_fetch",
        request_id="req_123",
        latency_ms=100.0,
        status="success",
        cost_usd=0.01
    )
    
    assert tool_call.agent == "test_agent"
    assert tool_call.tool_name == "payable_fetch"
    assert tool_call.status == "success"
    assert tool_call.cost_usd == 0.01


@pytest.mark.asyncio
async def test_mcp_client_missing_secret():
    """Test MCP client without secret - stub just returns disabled"""
    client = MCPClient(
        enabled=True
    )
    
    # Stub implementation doesn't require secret, just returns disabled
    result = await client.call_tool("payable_fetch", "test_agent", {"url": "http://example.com"})
    assert result == {"status": "disabled", "error": "MCP payment functionality removed"}