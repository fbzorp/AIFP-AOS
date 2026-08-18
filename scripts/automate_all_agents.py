#!/usr/bin/env python3
"""
DEMO SCRIPT: Automate all agents to make real and reasonable posts to their respective channels.
Each agent uses their specific Moltbook credentials and DeepSeek reasoning.

⚠️  WARNING: This is a DEMO script for testing purposes only.
- It creates content in PENDING_REVIEW status (requires human approval)
- It does NOT auto-approve or auto-publish content
- Set DEMO_MODE=true environment variable to run this script
- DO NOT use in production without explicit operator approval
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from apps.models.base import get_sync_session
from apps.models.content_item import ContentItemModel
from apps.agents.registry import get_agent

# Safety check: require DEMO_MODE=true
if os.environ.get("DEMO_MODE") != "true":
    print("❌ ERROR: This is a demo script. Set DEMO_MODE=true environment variable to run.")
    print("⚠️  This script creates PENDING_REVIEW content only - no auto-approval.")
    sys.exit(1)

async def automate_agent(agent_name: str, channel: str, objective: str):
    """Automate a single agent to create content in PENDING_REVIEW status."""
    print(f"🤖 Automating {agent_name}...")
    print("-" * 70)
    
    with get_sync_session() as session:
        try:
            # Create content item
            content = ContentItemModel(
                title=f'Demo Post - {agent_name}',
                body='',
                channel=channel,
                status='draft',
                objective=objective,
                target_audience='General audience',
                format='Blog post',
                author_agent=agent_name
            )
            session.add(content)
            session.commit()
            session.refresh(content)
            print(f"✅ Created content: {content.id}")
            
            # Execute agent to generate content with DeepSeek reasoning
            agent = get_agent(agent_name)
            if not agent:
                print(f"❌ Agent {agent_name} not found")
                return None
            
            print(f"🧠 Agent generating content with DeepSeek reasoning...")
            result = await agent.execute({"content_item_id": content.id})
            print(f"📝 Agent result: {result}")
            
            # Refresh content to get generated body
            session.refresh(content)
            
            # Set to pending_review for human approval (NO auto-approval)
            content.status = 'pending_review'
            session.commit()
            print(f"✅ Content set to PENDING_REVIEW (requires human approval)")
            
            return {
                "agent": agent_name,
                "success": True,
                "content_id": content.id,
                "title": content.title,
                "status": "pending_review"
            }
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "agent": agent_name,
                "success": False,
                "error": str(e)
            }

async def automate_all_agents():
    """Automate all major agents to create content in PENDING_REVIEW status."""
    print("="*70)
    print("🚀 DEMO: CREATING CONTENT IN PENDING_REVIEW STATUS")
    print("="*70)
    print("⚠️  Content requires human approval via the approvals API")
    print()
    
    # Define agents with their specific channels and objectives
    agent_configs = [
        {
            "name": "SEO Content",
            "channel": "google",
            "objective": "Generate SEO-optimized content about AI finance and DeFi"
        },
        {
            "name": "Founder Content", 
            "channel": "moltbook",
            "objective": "Share founder insights on AI fintech innovation and company vision"
        },
        {
            "name": "Technical Content",
            "channel": "moltbook", 
            "objective": "Create technical tutorials and development guides"
        }
    ]
    
    results = []
    
    for config in agent_configs:
        print()
        result = await automate_agent(
            config["name"],
            config["channel"],
            config["objective"]
        )
        if result:
            results.append(result)
        print()
    
    # Summary
    print("="*70)
    print("📊 DEMO SUMMARY")
    print("="*70)
    print()
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"Total agents: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print()
    
    if successful:
        print("🎉 SUCCESSFUL AGENTS (Content in PENDING_REVIEW):")
        for result in successful:
            print(f"✅ {result['agent']}")
            print(f"   📝 Content ID: {result.get('content_id')}")
            print(f"   � Status: {result.get('status')}")
            print(f"   📝 {result.get('title', 'N/A')}")
            print()
    
    if failed:
        print("❌ FAILED AGENTS:")
        for result in failed:
            print(f"❌ {result['agent']}")
            print(f"   Error: {result.get('error', 'Unknown')}")
            print()
    
    print("="*70)
    print("📋 NEXT STEPS")
    print("="*70)
    print()
    print("To approve and publish content, use the approvals API:")
    print("  POST /api/v1/content/{content_id}/approve")
    print("  POST /api/v1/content/{content_id}/publish")
    print()
    
    for result in successful:
        print(f"🔗 {result['agent']}: Content ID {result.get('content_id')}")
    
    print()
    return len(successful) == len(results)

if __name__ == "__main__":
    success = asyncio.run(automate_all_agents())
    sys.exit(0 if success else 1)