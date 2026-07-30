import asyncio
import logging

from apps.integrations.mcp.client import MCPClient
from apps.models.base import get_sync_session
from apps.models.audit_event import AuditEventModel
from apps.core.audit.service import record_event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def execute_mcp_calls_docker():
    """Execute 10 real MCP tool calls using the aifinpay-agent SDK.

    Uses a mix of local and network-backed tools for meaningful MCP calls:
    - agent_address: Local SDK call (always succeeds, no network required)
    - agent_quote: Network-backed SDK call (quotes payment split - may fail if API unavailable)
    - payable_fetch: Network-backed SDK call (fetches payable data - may fail if no payable ID)
    - agent_claim_self: Local SDK call (checks if agent has Seat PDA - may return False for devnet)

    The :class:`MCPClient` records audit events (``mcp_call_succeeded``
    or ``mcp_call_failed``) automatically. After the calls we query the
    database for the total number of successful events and print a summary.
    """
    logger.info("=== EXECUTING 10 REAL MCP CALLS ===")
    client = MCPClient(enabled=True)
    # Wait for MCP client to be ready (up to 5 attempts)
    async def _wait_for_mcp():
        for attempt in range(5):
            try:
                # simple health check: call agent_address (local SDK call)
                await client.call_tool("agent_address", agent="test_agent", params={})
                logger.info("MCP client is ready.")
                break
            except Exception as e:
                logger.warning(f"MCP not ready (attempt {attempt+1}/5): {e}")
                await asyncio.sleep(2 * (attempt + 1))
        else:
            logger.error("MCP client did not become ready after retries.")
    await _wait_for_mcp()
    results = []
    # Use mix of local and network-backed tools for meaningful MCP calls
    tools = [
        ("agent_address", {}),
        ("agent_quote", {"amount": 0.01, "chain": "solana"}),
        ("agent_address", {}),
        ("payable_fetch", {"url": "https://api.aifinpay.io/payables/example"}),
        ("agent_address", {}),
        ("agent_claim_self", {}),
        ("agent_address", {}),
        ("agent_quote", {"amount": 0.05, "chain": "solana"}),
        ("agent_address", {}),
        ("agent_claim_self", {})
    ]
    for i, (tool, params) in enumerate(tools):
        logger.info(f"\n--- MCP Call {i+1} ---")
        logger.info(f"Tool: {tool}")
        logger.info(f"Params: {params}")
        try:
            result = await client.call_tool(tool, agent="test_agent", params=params)
            logger.info(f"Result: {result}")
            results.append({"call_number": i+1, "tool": tool, "status": "success", "result": result})
        except Exception as e:
            logger.error(f"MCP Call {i+1} failed: {e}")
            results.append({"call_number": i+1, "tool": tool, "status": "failed", "error": str(e)})

    # Summarize audit events
    logger.info("\n=== CHECKING AUDIT EVENTS ===")
    with get_sync_session() as session:
        succeeded = session.query(AuditEventModel).filter(AuditEventModel.event_type == "mcp_call_succeeded").count()
        failed = session.query(AuditEventModel).filter(AuditEventModel.event_type == "mcp_call_failed").count()
        logger.info(f"Total mcp_call_succeeded events: {succeeded}")
        logger.info(f"Total mcp_call_failed events: {failed}")
        
        # Verify no succeeded events have error or mock_success fields
        succeeded_events = session.query(AuditEventModel).filter(AuditEventModel.event_type == "mcp_call_succeeded").all()
        for event in succeeded_events:
            metadata = event.metadata_json or {}
            if metadata.get("error"):
                logger.warning(f"⚠️ Succeeded event {event.id} has error field: {metadata.get('error')}")
            if metadata.get("status") == "mock_success":
                logger.warning(f"⚠️ Succeeded event {event.id} has mock_success status")
        
        if succeeded and not any((e.metadata_json or {}).get("error") for e in succeeded_events):
            logger.info("✅ All succeeded events have no error field (genuine SDK successes)")
    return results

if __name__ == "__main__":
    asyncio.run(execute_mcp_calls_docker())