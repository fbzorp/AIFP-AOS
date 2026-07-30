import httpx
import logging
import time
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MCPToolCall:
    """MCP tool call record"""
    agent: str
    tool_name: str
    request_id: str
    latency_ms: float
    status: str
    cost_usd: Optional[float] = None
    error: Optional[str] = None

class MCPClient:
    """Real MCP client that connects to the @aifinpay/mcp sidecar"""
    
    # MCP tools available
    AVAILABLE_TOOLS = [
        "payable_fetch",
        "agent_address", 
        "agent_quote",
        "agent_call",
        "pay_with_split",
        "quote_split",
        "agent_claim_self"
    ]
    
    def __init__(
        self,
        mcp_server_url: str = "http://aifinpay-mcp:3000",
        max_usd: float = 0.10,
        enabled: bool = False,
        timeout: float = 30
    ):
        self.mcp_server_url = mcp_server_url
        self.max_usd = max_usd
        self.enabled = enabled
        self.timeout = timeout
        self.http = httpx.AsyncClient(timeout=timeout)
        self._call_history: List[MCPToolCall] = []
        
        logger.info(f"MCPClient initialized (enabled={enabled}, max_usd={max_usd})")
    
    async def call_tool(
        self,
        tool_name: str,
        agent: str,
        params: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call an MCP tool and record the event"""
        if not self.enabled:
            logger.warning(f"MCP is disabled, skipping tool call: {tool_name}")
            return {"status": "disabled", "error": "MCP is disabled"}
        
        if tool_name not in self.AVAILABLE_TOOLS:
            raise ValueError(f"Unknown MCP tool: {tool_name}")
        
        request_id = request_id or f"req_{int(time.time() * 1000)}"
        start_time = time.time()
        
        try:
            logger.info(f"Calling MCP tool: {tool_name} for agent: {agent}")
            
            # Make HTTP request to MCP sidecar
            response = await self.http.post(
                f"{self.mcp_server_url}/tools/{tool_name}",
                json={
                    "params": params,
                    "request_id": request_id,
                    "agent": agent
                }
            )
            response.raise_for_status()
            result = response.json()
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract cost if available
            cost_usd = result.get("cost_usd", 0.001)
            
            # Check max USD cap
            if cost_usd and cost_usd > self.max_usd:
                logger.warning(f"Tool call cost {cost_usd} exceeds max_usd {self.max_usd}")
                raise ValueError(f"Cost {cost_usd} exceeds maximum allowed {self.max_usd}")
            
            # Record successful call in memory
            call_record = MCPToolCall(
                agent=agent,
                tool_name=tool_name,
                request_id=request_id,
                latency_ms=latency_ms,
                status="success",
                cost_usd=cost_usd
            )
            self._call_history.append(call_record)
            
            # Record as audit event in database
            await self._record_audit_event(call_record)
            
            logger.info(f"MCP tool call succeeded: {tool_name} (latency: {latency_ms:.2f}ms)")
            return result
            
        except httpx.HTTPStatusError as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"HTTP error: {e.response.status_code}"
            
            # Record failed call
            call_record = MCPToolCall(
                agent=agent,
                tool_name=tool_name,
                request_id=request_id,
                latency_ms=latency_ms,
                status="failed",
                error=error_msg
            )
            self._call_history.append(call_record)
            await self._record_audit_event(call_record)
            
            logger.error(f"MCP tool call failed: {tool_name} - {error_msg}")
            raise
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            # Record failed call
            call_record = MCPToolCall(
                agent=agent,
                tool_name=tool_name,
                request_id=request_id,
                latency_ms=latency_ms,
                status="failed",
                error=error_msg
            )
            self._call_history.append(call_record)
            await self._record_audit_event(call_record)
            
            logger.error(f"MCP tool call failed: {tool_name} - {error_msg}")
            raise
    
    async def _record_audit_event(self, call: MCPToolCall):
        """Record MCP call as audit event in database"""
        try:
            from apps.models.base import get_sync_session
            from apps.core.audit.service import record_event
            
            event_type = "mcp_call_succeeded" if call.status == "success" else "mcp_call_failed"
            description = f"MCP tool call {call.status}: {call.tool_name}"
            
            def _record():
                with get_sync_session() as session:
                    record_event(
                        session,
                        call.agent,
                        event_type,
                        description,
                        {
                            "tool_name": call.tool_name,
                            "request_id": call.request_id,
                            "latency_ms": call.latency_ms,
                            "cost_usd": call.cost_usd,
                            "status": call.status,
                            "error": call.error
                        }
                    )
                    session.commit()
            
            await asyncio.to_thread(_record)
            logger.info(f"Recorded audit event for MCP call: {call.tool_name} ({event_type})")
            
        except Exception as e:
            logger.error(f"Failed to record audit event for MCP call: {e}")
    
    async def payable_fetch(self, agent: str, payable_id: str) -> Dict[str, Any]:
        """Fetch payable information"""
        return await self.call_tool(
            "payable_fetch",
            agent,
            {"payable_id": payable_id}
        )
    
    async def agent_address(self, agent: str) -> Dict[str, Any]:
        """Get agent's wallet address"""
        return await self.call_tool(
            "agent_address",
            agent,
            {}
        )
    
    async def agent_quote(self, agent: str, amount: float, currency: str) -> Dict[str, Any]:
        """Get a quote for an agent operation"""
        return await self.call_tool(
            "agent_quote",
            agent,
            {"amount": amount, "currency": currency}
        )
    
    async def agent_call(self, agent: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an agent call"""
        return await self.call_tool(
            "agent_call",
            agent,
            {"method": method, "params": params}
        )
    
    async def pay_with_split(
        self,
        agent: str,
        merchant_wallet: str,
        amount: float,
        order_id: str
    ) -> Dict[str, Any]:
        """Execute payment with atomic split"""
        return await self.call_tool(
            "pay_with_split",
            agent,
            {
                "merchant_wallet": merchant_wallet,
                "amount": amount,
                "order_id": order_id
            }
        )
    
    async def quote_split(self, agent: str, amount: float, currency: str) -> Dict[str, Any]:
        """Get quote for split payment"""
        return await self.call_tool(
            "quote_split",
            agent,
            {"amount": amount, "currency": currency}
        )
    
    async def agent_claim_self(self, agent: str) -> Dict[str, Any]:
        """Claim self-referral bonus"""
        return await self.call_tool(
            "agent_claim_self",
            agent,
            {}
        )
    
    def get_call_history(self) -> List[MCPToolCall]:
        """Get history of MCP tool calls"""
        return self._call_history.copy()
    
    def get_successful_calls(self) -> List[MCPToolCall]:
        """Get only successful MCP tool calls"""
        return [call for call in self._call_history if call.status == "success"]
    
    async def close(self):
        await self.http.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()