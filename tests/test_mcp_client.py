import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from apps.integrations.mcp.client import MCPClient, MCPToolCall


@pytest.mark.asyncio
async def test_mcp_client_initialization():
    """Test MCP client initialization"""
    client = MCPClient(
        max_usd=100.0,
        enabled=True,
        timeout=30.0
    )
    
    assert client.max_usd == 100.0
    assert client.enabled is True
    assert client.timeout == 30.0
    assert len(client._call_history) == 0


@pytest.mark.asyncio
async def test_mcp_client_disabled():
    """Test MCP client when disabled"""
    client = MCPClient(
        max_usd=100.0,
        enabled=False
    )
    
    result = await client.call_tool("payable_fetch", "test_agent", {"url": "http://example.com"})
    assert result == {"status": "disabled", "error": "MCP is disabled"}


@pytest.mark.asyncio
async def test_mcp_client_available_tools():
    """Test getting available tools"""
    client = MCPClient(
        max_usd=100.0,
        enabled=True
    )
    
    tools = client.AVAILABLE_TOOLS
    assert len(tools) > 0
    assert "payable_fetch" in tools
    assert "agent_call" in tools


@pytest.mark.asyncio
async def test_mcp_client_unknown_tool():
    """Test MCP client with unknown tool"""
    client = MCPClient(
        max_usd=100.0,
        enabled=True
    )
    
    with pytest.raises(ValueError, match="Unknown MCP tool"):
        await client.call_tool("unknown_tool", "test_agent", {"param": "value"})


@pytest.mark.asyncio
async def test_mcp_client_context_manager():
    """Test MCP client async context manager"""
    async with MCPClient(
        max_usd=100.0,
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
    """Test MCP client initialization without secret"""
    client = MCPClient(
        max_usd=100.0,
        enabled=True
    )
    
    with patch.dict('os.environ', {}, clear=True):
        client.agent_secret = None
        
        with pytest.raises(RuntimeError, match="AIFINPAY_AGENT_SECRET environment variable is required"):
            await client.call_tool("payable_fetch", "test_agent", {"url": "http://example.com"})