#!/usr/bin/env python3
"""
DEMO SCRIPT: Automate a single agent to create content in PENDING_REVIEW status.
Usage: DEMO_MODE=true python scripts/automate_single_agent.py --agent "SEO Content"

⚠️  WARNING: This is a DEMO script for testing purposes only.
- It creates content in PENDING_REVIEW status (requires human approval)
- It does NOT auto-approve or auto-publish content
- Set DEMO_MODE=true environment variable to run this script
- DO NOT use in production without explicit operator approval
"""

import os
import sys
import argparse
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

async def automate_agent(agent_name: str):
    """Automate a single agent to create content in PENDING_REVIEW status."""
    print("="*70)
    print(f"🚀 DEMO: CREATING CONTENT FOR {agent_name.upper()}")
    print("="*70)
    print("⚠️  Content will be in PENDING_REVIEW status (requires human approval)")
    print()
    
    # Define channel and objective based on agent
    agent_configs = {
        "SEO Content": {
            "channel": "google",
            "objective": "Generate SEO-optimized content about AI finance and DeFi"
        },
        "Founder Content": {
            "channel": "moltbook",
            "objective": "Share founder insights on AI fintech innovation and company vision"
        },
        "Technical Content": {
            "channel": "moltbook",
            "objective": "Create technical tutorials and development guides"
        }
    }
    
    if agent_name not in agent_configs:
        print(f"❌ Unknown agent: {agent_name}")
        print(f"Available agents: {list(agent_configs.keys())}")
        return False
    
    config = agent_configs[agent_name]
    channel = config["channel"]
    objective = config["objective"]
    
    print(f"📋 Configuration:")
    print(f"   Channel: {channel}")
    print(f"   Objective: {objective}")
    print()
    
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
                return False
            
            print(f"🧠 Agent generating content with DeepSeek reasoning...")
            result = await agent.execute({"content_item_id": content.id})
            print(f"📝 Agent result: {result}")
            
            # Refresh content to get generated body
            session.refresh(content)
            
            # Set to pending_review for human approval (NO auto-approval)
            content.status = 'pending_review'
            session.commit()
            print(f"✅ Content set to PENDING_REVIEW (requires human approval)")
            
            print()
            print("="*70)
            print("📋 NEXT STEPS")
            print("="*70)
            print()
            print(f"Content ID: {content.id}")
            print(f"Status: pending_review")
            print()
            print("To approve and publish content, use the approvals API:")
            print(f"  POST /api/v1/content/{content.id}/approve")
            print(f"  POST /api/v1/content/{content.id}/publish")
            print()
            return True
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    parser = argparse.ArgumentParser(description="Automate a single agent")
    parser.add_argument("--agent", required=True, help="Agent name (e.g., 'SEO Content', 'Founder Content', 'Technical Content')")
    args = parser.parse_args()
    
    success = asyncio.run(automate_agent(args.agent))
    
    if success:
        print("🎉 Agent automation completed successfully!")
    else:
        print("⚠️  Agent automation failed")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()