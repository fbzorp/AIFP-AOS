#!/usr/bin/env python3
"""
Moltbook Credential Verification Script

This script tests Moltbook credentials for specific agents to verify they work correctly.
It will:
1. Test identity token creation
2. Test identity verification  
3. Attempt a test post (optional)
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.api.config import settings
from apps.integrations.moltbook.client import MoltbookClient
from apps.core.credential.service import CredentialService

# Most important social agents for Moltbook
IMPORTANT_SOCIAL_AGENTS = [
    "SEO Content",
    "Founder Content", 
    "Technical Content",
    "Social Publishing Agent",
    "Community Engagement Agent"
]

async def test_agent_credentials(agent_name: str, test_post: bool = False):
    """Test Moltbook credentials for a specific agent."""
    print(f"\n🔍 Testing Moltbook credentials for: {agent_name}")
    print("-" * 60)
    
    try:
        # Get credentials for this agent
        creds = CredentialService.get_moltbook_credentials_sync(agent_name)
        
        print(f"  Agent API Key: {creds.get('agent_api_key', 'NOT SET')[:20]}...")
        print(f"  App Key: {creds.get('app_key', 'NOT SET')[:20]}...")
        
        if not creds.get('agent_api_key'):
            print("  ❌ No agent API key found")
            return False
        
        # Create client
        client = MoltbookClient(
            agent_key=creds.get('agent_api_key'),
            app_key=creds.get('app_key'),
            timeout=20
        )
        
        # Test identity token creation
        print("  📝 Testing identity token creation...")
        try:
            token_data = await client.create_identity_token()
            print(f"  ✅ Identity token created successfully")
            print(f"     Agent ID: {token_data.get('agentId')}")
            print(f"     Agent Name: {token_data.get('agentName')}")
            print(f"     Expires: {token_data.get('expiresAt')}")
        except Exception as e:
            print(f"  ❌ Identity token creation failed: {e}")
            await client.close()
            return False
        
        # Test identity verification
        print("  🔐 Testing identity verification...")
        try:
            token = token_data.get('token')
            if token:
                agent_data = await client.verify_identity(token)
                print(f"  ✅ Identity verified successfully")
                print(f"     Verified Agent: {agent_data}")
            else:
                print(f"  ❌ No token in response")
                await client.close()
                return False
        except Exception as e:
            print(f"  ❌ Identity verification failed: {e}")
            await client.close()
            return False
        
        # Optional test post
        if test_post:
            print("  📤 Testing post creation...")
            try:
                result = await client.publish_post(
                    submolt='general',
                    title=f'Credential Test - {agent_name}',
                    body=f'This is a test post to verify Moltbook credentials for {agent_name}. If you see this, credentials are working correctly.'
                )
                print(f"  ✅ Test post created successfully")
                print(f"     Post ID: {result.get('post_id')}")
                print(f"     Post URL: {result.get('post_url')}")
                print(f"     Dry Run: {result.get('dry_run')}")
            except Exception as e:
                print(f"  ❌ Test post creation failed: {e}")
                await client.close()
                return False
        
        await client.close()
        print(f"  ✅ All tests passed for {agent_name}")
        return True
        
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_global_credentials(test_post: bool = False):
    """Test global Moltbook credentials."""
    print(f"\n🔍 Testing GLOBAL Moltbook credentials")
    print("-" * 60)
    
    try:
        if not settings.MOLTBOOK_AGENT_API_KEY:
            print("  ❌ No global MOLTBOOK_AGENT_API_KEY found")
            return False
        
        print(f"  Agent API Key: {settings.MOLTBOOK_AGENT_API_KEY[:20]}...")
        print(f"  App Key: {settings.MOLTBOOK_APP_KEY[:20]}...")
        
        # Create client
        client = MoltbookClient(
            agent_key=settings.MOLTBOOK_AGENT_API_KEY,
            app_key=settings.MOLTBOOK_APP_KEY,
            timeout=20
        )
        
        # Test identity token creation
        print("  📝 Testing identity token creation...")
        try:
            token_data = await client.create_identity_token()
            print(f"  ✅ Identity token created successfully")
            print(f"     Agent ID: {token_data.get('agentId')}")
            print(f"     Agent Name: {token_data.get('agentName')}")
        except Exception as e:
            print(f"  ❌ Identity token creation failed: {e}")
            await client.close()
            return False
        
        # Test identity verification
        print("  🔐 Testing identity verification...")
        try:
            token = token_data.get('token')
            if token:
                agent_data = await client.verify_identity(token)
                print(f"  ✅ Identity verified successfully")
            else:
                print(f"  ❌ No token in response")
                await client.close()
                return False
        except Exception as e:
            print(f"  ❌ Identity verification failed: {e}")
            await client.close()
            return False
        
        await client.close()
        print(f"  ✅ Global credentials test passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

async def main():
    """Main verification function."""
    print("🔍 MOLTBOOK CREDENTIAL VERIFICATION")
    print("="*70)
    
    # Ask what to test
    print("\nWhat would you like to test?")
    print("1. Global credentials only")
    print("2. Specific agent credentials")
    print("3. All agent credentials")
    print("4. All credentials (global + all agents)")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    test_post = input("\nInclude test post creation? (yes/no, default: no): ").strip().lower()
    test_post = test_post in ["yes", "y"]
    
    if test_post:
        print("⚠️  WARNING: Test posts will be created on Moltbook!")
        confirm = input("Are you sure? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            test_post = False
    
    results = {}
    
    if choice == "1":
        results["Global"] = await test_global_credentials(test_post)
    
    elif choice == "2":
        print("\nAvailable agents:")
        for i, agent in enumerate(IMPORTANT_SOCIAL_AGENTS, 1):
            print(f"  {i}. {agent}")
        
        agent_choice = input("\nEnter agent number: ").strip()
        try:
            idx = int(agent_choice) - 1
            if 0 <= idx < len(IMPORTANT_SOCIAL_AGENTS):
                agent_name = IMPORTANT_SOCIAL_AGENTS[idx]
                results[agent_name] = await test_agent_credentials(agent_name, test_post)
            else:
                print("❌ Invalid agent number")
        except ValueError:
            print("❌ Invalid input")
    
    elif choice == "3":
        for agent_name in IMPORTANT_SOCIAL_AGENTS:
            results[agent_name] = await test_agent_credentials(agent_name, test_post)
    
    elif choice == "4":
        results["Global"] = await test_global_credentials(test_post)
        for agent_name in IMPORTANT_SOCIAL_AGENTS:
            results[agent_name] = await test_agent_credentials(agent_name, test_post)
    
    else:
        print("❌ Invalid choice")
        return
    
    # Summary
    print("\n" + "="*70)
    print("📊 VERIFICATION SUMMARY")
    print("="*70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All credentials are working correctly!")
    else:
        print("⚠️  Some credentials need attention. Please review the failed tests above.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Verification cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)