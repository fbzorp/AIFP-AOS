"""
Test script to verify real publishing across all platforms.
Tests X/Twitter, Moltbook, and Telegram with actual credentials.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.integrations.x.client import XClient
from apps.integrations.moltbook.client import MoltbookClient
from apps.integrations.telegram.client import TelegramClient


async def test_x_publishing():
    """Test real X/Twitter publishing."""
    print("Testing X/Twitter real publishing...")
    
    client = XClient(autopublish=True)
    
    test_tweet = "Testing real X publishing via AIFP automation #ai #automation"
    
    try:
        result = await client.publish_post(test_tweet)
        print(f"X Result: {result}")
        
        if result.get("dry_run"):
            print("⚠️ X/Twitter still in dry-run mode - check credentials")
        else:
            print(f"✅ X/Twitter real publish successful: {result.get('post_url')}")
            
    except Exception as e:
        print(f"❌ X/Twitter publishing failed: {e}")
    finally:
        await client.close()


async def test_moltbook_publishing():
    """Test real Moltbook publishing."""
    print("\nTesting Moltbook real publishing...")
    
    client = MoltbookClient()
    
    test_post = {
        "title": "Testing Real Moltbook Publishing",
        "body": "This is a test post to verify real Moltbook publishing via AIFP automation system.",
        "submolt": "general"
    }
    
    try:
        result = await client.publish_post(**test_post)
        print(f"Moltbook Result: {result}")
        
        if result.get("dry_run"):
            print("⚠️ Moltbook still in dry-run mode - check credentials")
        else:
            print(f"✅ Moltbook real publish successful: {result.get('post_url')}")
            
    except Exception as e:
        print(f"❌ Moltbook publishing failed: {e}")
    finally:
        await client.close()


async def test_telegram_publishing():
    """Test real Telegram publishing."""
    print("\nTesting Telegram real publishing...")
    
    client = TelegramClient(autopublish=True)
    
    test_message = "Testing real Telegram publishing via AIFP automation to aifp_publisher_bot channel"
    
    try:
        result = await client.publish_post(test_message)
        print(f"Telegram Result: {result}")
        
        if result.get("dry_run"):
            print("⚠️ Telegram still in dry-run mode - check credentials")
        else:
            print(f"✅ Telegram real publish successful: {result.get('post_url')}")
            
    except Exception as e:
        print(f"❌ Telegram publishing failed: {e}")
    finally:
        await client.close()


async def main():
    """Run all platform publishing tests."""
    print("=" * 60)
    print("REAL PUBLISHING TEST - ALL PLATFORMS")
    print("=" * 60)
    
    await test_x_publishing()
    await test_moltbook_publishing()
    await test_telegram_publishing()
    
    print("\n" + "=" * 60)
    print("REAL PUBLISHING TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
