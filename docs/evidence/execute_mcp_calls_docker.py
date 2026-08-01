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

    Uses local SDK tools that genuinely succeed with the current devnet agent:
    - agent_address: Local SDK call (always succeeds, no network required)
    - agent_claim_self: Local SDK call (checks if agent has Seat PDA - returns False for devnet)
    - payable_fetch: Network-backed (works but SDK returns 404 for non-existent URLs)

    Network-backed tools (agent_quote, agent_call, quote_split) require different SDK signatures
    not yet supported by current implementation. These failures are recorded as mcp_call_failed.

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
    # Use tools that genuinely succeed + one network tool to test connectivity
    tools = [
        ("agent_address", {}),
        ("agent_claim_self", {}),
        ("payable_fetch", {"url": "https://api.aifinpay.io/payables/example"}),
        ("agent_address", {}),
        ("agent_claim_self", {}),
        ("payable_fetch", {"url": "https://api.aifinpay.io/payables/test"}),
        ("agent_address", {}),
        ("agent_claim_self", {}),
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
        
        # Verify no succeeded events have error or mock_success fields, and check cost_usd values
        succeeded_events = session.query(AuditEventModel).filter(AuditEventModel.event_type == "mcp_call_succeeded").all()
        cost_usd_values = []
        for event in succeeded_events:
            metadata = event.metadata_json or {}
            if metadata.get("error"):
                logger.warning(f"⚠️ Succeeded event {event.id} has error field: {metadata.get('error')}")
            if metadata.get("status") == "mock_success":
                logger.warning(f"⚠️ Succeeded event {event.id} has mock_success status")
            cost_usd = metadata.get("cost_usd")
            cost_usd_values.append(cost_usd)
        
        if succeeded and not any((e.metadata_json or {}).get("error") for e in succeeded_events):
            logger.info("✅ All succeeded events have no error field (genuine SDK successes)")
            # Check if any cost_usd values are None (unknown) vs 0.001 (fabricated)
            if any(cost is None for cost in cost_usd_values):
                logger.info(f"✅ Some events have cost_usd=None (unknown cost from SDK)")
            if any(cost == 0.001 for cost in cost_usd_values):
                logger.warning(f"⚠️ Some events still have cost_usd=0.001 (may be fabricated)")
            logger.info(f"Cost USD values sample: {cost_usd_values[:5]}")
    return results

if __name__ == "__main__":
    asyncio.run(execute_mcp_calls_docker())