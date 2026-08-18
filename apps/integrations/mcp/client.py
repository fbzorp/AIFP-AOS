import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MCPToolCall:
    """MCP tool call record (stub for payment removal)"""
    agent: str
    tool_name: str
    request_id: str
    latency_ms: float
    status: str
    cost_usd: Optional[float] = None
    error: Optional[str] = None

class MCPClient:
    """Stub MCP client - payment functionality removed"""
    
    def __init__(
        self,
        enabled: bool = False,
        timeout: float = 30
    ):
        self.enabled = enabled
        self.timeout = timeout
        self._call_history: List[MCPToolCall] = []
        logger.info(f"MCPClient initialized (enabled={enabled}) - payment functionality removed")
    
    async def call_tool(
        self,
        tool_name: str,
        agent: str,
        params: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """MCP tool calls disabled after payment removal"""
        logger.warning(f"MCP is disabled (payment code removed), skipping tool call: {tool_name}")
        return {"status": "disabled", "error": "MCP payment functionality removed"}
    
    async def payable_fetch(self, agent: str, payable_id: str) -> Dict[str, Any]:
        """Stub - payment functionality removed"""
        return await self.call_tool("payable_fetch", agent, {"payable_id": payable_id})
    
    async def agent_address(self, agent: str) -> Dict[str, Any]:
        """Stub - payment functionality removed"""
        return await self.call_tool("agent_address", agent, {})
    
    async def agent_quote(self, agent: str, amount: float, currency: str) -> Dict[str, Any]:
        """Stub - payment functionality removed"""
        return await self.call_tool("agent_quote", agent, {"amount": amount, "currency": currency})
    
    async def agent_call(self, agent: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stub - payment functionality removed"""
        return await self.call_tool("agent_call", agent, {"method": method, "params": params})
    
    async def pay_with_split(
        self,
        agent: str,
        merchant_wallet: str,
        amount: float,
        order_id: str
    ) -> Dict[str, Any]:
        """Stub - payment functionality removed"""
        return await self.call_tool("pay_with_split", agent, {
            "merchant_wallet": merchant_wallet,
            "amount": amount,
            "order_id": order_id
        })
    
    async def quote_split(self, agent: str, amount: float, currency: str) -> Dict[str, Any]:
        """Stub - payment functionality removed"""
        return await self.call_tool("quote_split", agent, {"amount": amount, "currency": currency})
    
    async def agent_claim_self(self, agent: str) -> Dict[str, Any]:
        """Stub - payment functionality removed"""
        return await self.call_tool("agent_claim_self", agent, {})
    
    def get_call_history(self) -> List[MCPToolCall]:
        """Get history of MCP tool calls"""
        return self._call_history.copy()
    
    def get_successful_calls(self) -> List[MCPToolCall]:
        """Get only successful MCP tool calls"""
        return [call for call in self._call_history if call.status == "success"]
    
    async def close(self):
        """Close the MCP client (no-op)"""
        pass
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
