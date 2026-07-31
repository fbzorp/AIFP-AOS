import logging
import time
import asyncio
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from aifinpay import Agent

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
    """Real MCP client that uses the aifinpay-agent Python SDK"""
    
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
        max_usd: float = 0.10,
        enabled: bool = False,
        timeout: float = 30
    ):
        self.max_usd = max_usd
        self.enabled = enabled
        self.timeout = timeout
        self._call_history: List[MCPToolCall] = []
        self._agent: Optional[Agent] = None
        self._initialized = False
        
        # Environment variables for aifinpay-agent
        self.agent_secret = os.getenv("AIFINPAY_AGENT_SECRET")
        
        logger.info(f"MCPClient initialized (enabled={enabled}, max_usd={max_usd})")
    
    async def _ensure_agent(self):
        """Ensure aifinpay-agent is initialized"""
        if self._initialized and self._agent:
            return
        
        if not self.agent_secret:
            raise RuntimeError("AIFINPAY_AGENT_SECRET environment variable is required")
        
        logger.info("Initializing aifinpay-agent...")
        
        # Initialize the aifinpay-agent SDK
        self._agent = Agent.from_secret_b58(self.agent_secret)
        self._initialized = True
        
        logger.info("aifinpay-agent initialized successfully")
    
    async def call_tool(
        self,
        tool_name: str,
        agent: str,
        params: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call an MCP tool using aifinpay-agent SDK and record the event"""
        if not self.enabled:
            logger.warning(f"MCP is disabled, skipping tool call: {tool_name}")
            return {"status": "disabled", "error": "MCP is disabled"}
        
        if tool_name not in self.AVAILABLE_TOOLS:
            raise ValueError(f"Unknown MCP tool: {tool_name}")
        
        request_id = request_id or f"req_{int(time.time() * 1000)}"
        start_time = time.time()
        
        try:
            logger.info(f"Calling MCP tool: {tool_name} for agent: {agent}")
            
            # Ensure agent is initialized
            await self._ensure_agent()
            
            # Call the appropriate aifinpay-agent method
            result = await self._call_agent_method(tool_name, params)
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract cost if available (default to None for "cost unknown")
            cost_usd = result.get("cost_usd")
            
            # Check max USD cap (only if cost is known and not None)
            if cost_usd is not None and cost_usd > self.max_usd:
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
            
            # Return the result in a compatible format
            return {
                "content": [
                    {
                        "type": "text",
                        "text": str(result)
                    }
                ],
                "isError": False
            }
            
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
    
    async def _call_agent_method(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call the appropriate aifinpay-agent method"""
        if tool_name == "agent_address":
            # This is a simple SDK call that doesn't require network access
            return {
                "address": str(self._agent.address),
                "solana_address": str(self._agent.address),
                "evm_address": str(self._agent.address),
                "cost_usd": None  # Local SDK call has no cost
            }
        elif tool_name == "agent_quote":
            # Direct SDK call - will raise on failure
            amount = params.get("amount", 0.01)
            chain = params.get("chain", "solana")
            # quote_split takes positional arguments, not keyword arguments
            result = self._agent.quote_split(amount, chain)
            # Extract real quote_id from SDK response if available
            quote_id = getattr(result, 'id', None) or getattr(result, 'quote_id', None) or f"q_{int(time.time() * 1000)}"
            # Extract real cost from SDK response if available
            cost_usd = getattr(result, 'cost_usd', None) or getattr(result, 'cost', None)
            return {
                "quote_id": quote_id,
                "amount": amount,
                "currency": "USD",
                "cost_usd": cost_usd,
                "sdk_result": str(result)
            }
        elif tool_name == "payable_fetch":
            # Direct SDK call - will raise on failure
            url = params.get("url", "")
            if not url:
                raise ValueError("url parameter is required for payable_fetch")
            # Agent.get() is synchronous, not async
            result = self._agent.get(url)
            # Extract real cost from SDK response if available
            cost_usd = getattr(result, 'cost_usd', None) or getattr(result, 'cost', None)
            return {
                "url": url,
                "status": "success",
                "cost_usd": cost_usd,
                "sdk_result": str(result)
            }
        elif tool_name == "agent_call":
            # Direct SDK call - will raise on failure
            url = params.get("url", "")
            body = params.get("body", {})
            if not url:
                raise ValueError("url parameter is required for agent_call")
            # Agent.post() is synchronous, not async - takes 2 positional args (url, body)
            result = self._agent.post(url, body)
            # Extract real cost from SDK response if available
            cost_usd = getattr(result, 'cost_usd', None) or getattr(result, 'cost', None)
            return {
                "url": url,
                "method": "POST",
                "status": "success",
                "cost_usd": cost_usd,
                "sdk_result": str(result)
            }
        elif tool_name == "pay_with_split":
            # Direct SDK call - will raise on failure
            merchant = params.get("merchant", "")
            amount = params.get("amount", 0.01)
            order_id = params.get("order_id", "")
            chain = params.get("chain", "solana")
            # pay_with_split_invoice takes keyword arguments
            result = self._agent.pay_with_split_invoice(merchant=merchant, amount=amount, order_id=order_id, chain=chain)
            # Extract real order_id from SDK response if available
            real_order_id = getattr(result, 'id', None) or getattr(result, 'order_id', None) or order_id
            # Extract real cost from SDK response if available
            cost_usd = getattr(result, 'cost_usd', None) or getattr(result, 'cost', None)
            return {
                "order_id": real_order_id,
                "merchant": merchant,
                "amount": amount,
                "chain": chain,
                "cost_usd": cost_usd,
                "sdk_result": str(result)
            }
        elif tool_name == "quote_split":
            # Direct SDK call - will raise on failure
            amount = params.get("amount", 0.01)
            chain = params.get("chain", "solana")
            # quote_split takes positional arguments, not keyword arguments
            result = self._agent.quote_split(amount, chain)
            # Extract real quote_id from SDK response if available
            quote_id = getattr(result, 'id', None) or getattr(result, 'quote_id', None) or f"qs_{int(time.time() * 1000)}"
            # Extract real cost from SDK response if available
            cost_usd = getattr(result, 'cost_usd', None) or getattr(result, 'cost', None)
            return {
                "quote_id": quote_id,
                "amount": amount,
                "chain": chain,
                "cost_usd": cost_usd,
                "sdk_result": str(result)
            }
        elif tool_name == "agent_claim_self":
            # Direct SDK call - has_seat() returns boolean, not awaitable
            has_seat = self._agent.has_seat()
            return {
                "claimed": has_seat,
                "has_seat": has_seat,
                "cost_usd": None  # Local SDK call has no cost
            }
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
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
        """Close the aifinpay-agent"""
        if self._agent:
            try:
                # Agent doesn't have explicit close, just reset references
                logger.info("aifinpay-agent cleanup complete")
            except Exception as e:
                logger.error(f"Error during aifinpay-agent cleanup: {e}")
            finally:
                self._agent = None
                self._initialized = False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()