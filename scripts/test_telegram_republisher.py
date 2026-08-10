"""
Test script to verify Telegram Republisher agent functionality.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.agents.telegram_republisher import TelegramRepublisherAgent


async def main():
    """Test the Telegram Republisher agent."""
    print("Testing Telegram Republisher Agent...")
    
    agent = TelegramRepublisherAgent()
    print(f"Agent Name: {agent.name}")
    print(f"Agent Role: {agent.role}")
    print(f"Agent Description: {agent.description}")
    print(f"Agent Capabilities: {agent.get_capabilities()}")
    
    # Test auto-discovery and republishing
    print("\nTesting auto-discovery and republishing...")
    result = await agent.execute({})
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
