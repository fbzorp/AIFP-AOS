"""
Execute 10 real MCP tool calls inside Docker environment
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.integrations.mcp.client import MCPClient
from apps.api.config import settings
from apps.models.base import get_sync_session
from apps.models.audit_event import AuditEventModel
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def execute_mcp_calls():
    """Execute 10 real MCP tool calls"""
    logger.info("Starting 10 real MCP tool calls...")
    
    mcp_client = MCPClient(
        mcp_server_url="http://aifinpay-mcp:3000",
        enabled=True  # Enable MCP for testing
    )
    
    tools_to_call = [
        "agent_address",
        "agent_quote", 
        "payable_fetch",
        "agent_address",
        "agent_quote",
        "payable_fetch",
        "agent_address",
        "agent_quote",
        "payable_fetch",
        "agent_address"
    ]
    
    results = []
    for i, tool_name in enumerate(tools_to_call, 1):
        try:
            logger.info(f"MCP Call {i}: {tool_name}")
            
            params = {}
            if tool_name == "agent_address":
                params = {}
            elif tool_name == "agent_quote":
                params = {"amount": 0.01, "currency": "SOL"}
            elif tool_name == "payable_fetch":
                params = {"payable_id": f"test_invoice_{i}"}
            
            result = await mcp_client.call_tool(
                tool_name=tool_name,
                agent="test_agent",
                params=params,
                request_id=f"req_{i}"
            )
            
            logger.info(f"MCP Call {i} SUCCESS: {result}")
            results.append({"call": i, "tool": tool_name, "status": "success", "result": result})
            
        except Exception as e:
            logger.error(f"MCP Call {i} FAILED: {e}")
            results.append({"call": i, "tool": tool_name, "status": "failed", "error": str(e)})
    
    await mcp_client.close()
    
    # Query database for audit events
    logger.info("\nQuerying database for MCP audit events...")
    with get_sync_session() as session:
        mcp_audit_events = session.execute(
            select(AuditEventModel).filter(
                AuditEventModel.event_type == "mcp_call_succeeded"
            )
        ).scalars().all()
        
        total_count = len(mcp_audit_events)
        logger.info(f"Total mcp_call_succeeded audit events: {total_count}")
        
        if mcp_audit_events:
            logger.info("\nSample MCP audit events:")
            for event in mcp_audit_events[-5:]:  # Show last 5
                # Handle metadata as SQLAlchemy MetaData object
                try:
                    metadata = dict(event.metadata) if hasattr(event.metadata, '__iter__') else {}
                except:
                    metadata = {}
                
                tool_name = metadata.get('tool_name') if isinstance(metadata, dict) else 'N/A'
                request_id = metadata.get('request_id') if isinstance(metadata, dict) else 'N/A'
                latency_ms = metadata.get('latency_ms') if isinstance(metadata, dict) else 'N/A'
                
                logger.info(f"  - ID: {event.id}, Tool: {tool_name}, Request ID: {request_id}, Latency: {latency_ms}ms")
    
    logger.info(f"\nMCP Call Summary:")
    success_count = sum(1 for r in results if r["status"] == "success")
    logger.info(f"Successful calls: {success_count}/10")
    logger.info(f"Failed calls: {10 - success_count}/10")
    
    return results, total_count

if __name__ == "__main__":
    results, total_count = asyncio.run(execute_mcp_calls())
    print(f"\nMCP calls completed. Total audit events: {total_count}")