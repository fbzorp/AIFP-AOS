#!/usr/bin/env python3
"""
Automate a single agent to make real and reasonable posts to their respective channel.
Usage: python scripts/automate_single_agent.py --agent "SEO Content"
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from apps.models.base import get_sync_session
from apps.models.content_item import ContentItemModel
from apps.models.approval import ApprovalModel
from apps.core.policy.engine import compute_draft_hash
from apps.agents.registry import get_agent

async def automate_agent(agent_name: str):
    """Automate a single agent to create and publish content."""
    print("="*70)
    print(f"🚀 AUTOMATING {agent_name.upper()}")
    print("="*70)
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
            "objective": "Create technical tutorials and development guides for AiFinPay"
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
                title=f'Autonomous Post - {agent_name}',
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
            
            # Auto-approve
            draft_hash = compute_draft_hash(content)
            approval = ApprovalModel(
                content_id=content.id,
                status='approved',
                approved_by='System Automation',
                draft_hash=draft_hash
            )
            session.add(approval)
            content.status = 'approved'
            session.commit()
            print(f"✅ Auto-approved content")
            
            # Publish
            from apps.workers.tasks import _perform_publish_logic
            result = await _perform_publish_logic(session, content.id, approval.id, draft_hash)
            print(f"📤 Publishing result: {result.get('status')}")
            
            if result.get("status") == "published":
                url = result.get("post_url")
                post_id = result.get("post_id")
                
                # Generate clickable URL
                if url:
                    print(f"✅ SUCCESS: Live URL: {url}")
                    print()
                    print("="*70)
                    print("📋 VERIFICATION URL")
                    print("="*70)
                    print(f"🔗 {url}")
                    print()
                    return True
                elif post_id and channel == "moltbook":
                    api_url = f"https://www.moltbook.com/api/v1/posts/{post_id}"
                    print(f"✅ SUCCESS: API URL: {api_url}")
                    print()
                    print("="*70)
                    print("📋 VERIFICATION URL")
                    print("="*70)
                    print(f"🔗 {api_url}")
                    print()
                    return True
                elif post_id and channel == "telegram":
                    telegram_url = f"https://t.me/c/{post_id}"
                    print(f"✅ SUCCESS: Telegram URL: {telegram_url}")
                    print()
                    print("="*70)
                    print("📋 VERIFICATION URL")
                    print("="*70)
                    print(f"🔗 {telegram_url}")
                    print()
                    return True
                else:
                    print(f"✅ SUCCESS: Post ID {post_id}")
                    return True
            else:
                print(f"❌ FAILED: {result}")
                return False
                
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