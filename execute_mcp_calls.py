"""Canonical MCP execution script alias.
Delegates directly to execute_mcp_calls_docker.py to ensure single source of truth.
"""
import asyncio
from execute_mcp_calls_docker import execute_mcp_calls_docker

if __name__ == "__main__":
    asyncio.run(execute_mcp_calls_docker())