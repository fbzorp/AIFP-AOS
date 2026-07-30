import asyncio
import logging

from apps.integrations.mcp.client import MCPClient
from apps.models.base import get_sync_session
from apps.models.audit_event import AuditEventModel
from apps.core.audit.service import record_event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def execute_mcp_calls_docker():
    """Execute 10 real MCP tool calls against the sidecar.

    The :class:`MCPClient` records audit events (``mcp_call_succeeded``
    or ``mcp_call_failed``) automatically. After the calls we query the
    database for the total number of successful events and print a summary.
    """
    logger.info("=== EXECUTING 10 REAL MCP CALLS ===")
    client = MCPClient(enabled=True)
    # Wait for MCP sidecar to be ready (up to 5 attempts)
    async def _wait_for_mcp():
        for attempt in range(5):
            try:
                # simple health check: call a lightweight tool with empty params
                await client.call_tool("agent_address", agent="test_agent", params={})
                logger.info("MCP sidecar is reachable.")
                break
            except Exception as e:
                logger.warning(f"MCP not ready (attempt {attempt+1}/5): {e}")
                await asyncio.sleep(2 * (attempt + 1))
        else:
            logger.error("MCP sidecar did not become reachable after retries.")
    await _wait_for_mcp()
    results = []
    tools = ["agent_address", "agent_quote", "payable_fetch"]
    for i in range(10):
        tool = tools[i % len(tools)]
        logger.info(f"\n--- MCP Call {i+1} ---")
        logger.info(f"Tool: {tool}")
        try:
            result = await client.call_tool(tool, agent="test_agent", params={})
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
    return results

if __name__ == "__main__":
    asyncio.run(execute_mcp_calls_docker())