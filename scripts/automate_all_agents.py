#!/usr/bin/env python3
"""
Automate all agents to make real and reasonable posts to their respective channels.
Each agent uses their specific Moltbook credentials and DeepSeek reasoning.
"""

import sys
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

async def automate_agent(agent_name: str, channel: str, objective: str):
    """Automate a single agent to create and publish content."""
    print(f"🤖 Automating {agent_name}...")
    print("-" * 70)
    
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
                return None
            
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
                    return {
                        "agent": agent_name,
                        "success": True,
                        "url": url,
                        "post_id": post_id,
                        "title": content.title
                    }
                elif post_id and channel == "moltbook":
                    api_url = f"https://www.moltbook.com/api/v1/posts/{post_id}"
                    print(f"✅ SUCCESS: API URL: {api_url}")
                    return {
                        "agent": agent_name,
                        "success": True,
                        "url": api_url,
                        "post_id": post_id,
                        "title": content.title
                    }
                elif post_id and channel == "telegram":
                    telegram_url = f"https://t.me/c/{post_id}"
                    print(f"✅ SUCCESS: Telegram URL: {telegram_url}")
                    return {
                        "agent": agent_name,
                        "success": True,
                        "url": telegram_url,
                        "post_id": post_id,
                        "title": content.title
                    }
                else:
                    print(f"✅ SUCCESS: Post ID {post_id}")
                    return {
                        "agent": agent_name,
                        "success": True,
                        "post_id": post_id,
                        "title": content.title
                    }
            else:
                print(f"❌ FAILED: {result}")
                return {
                    "agent": agent_name,
                    "success": False,
                    "error": result
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
    """Automate all major agents to publish real content."""
    print("="*70)
    print("🚀 AUTOMATING ALL AGENTS WITH REAL CONTENT")
    print("="*70)
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
            "objective": "Create technical tutorials and development guides for AiFinPay"
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
    print("📊 AUTOMATION SUMMARY")
    print("="*70)
    print()
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"Total agents: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print()
    
    if successful:
        print("🎉 SUCCESSFUL AGENTS:")
        for result in successful:
            print(f"✅ {result['agent']}")
            if result.get("url"):
                print(f"   🔗 {result['url']}")
            print(f"   📝 {result.get('title', 'N/A')}")
            print()
    
    if failed:
        print("❌ FAILED AGENTS:")
        for result in failed:
            print(f"❌ {result['agent']}")
            print(f"   Error: {result.get('error', 'Unknown')}")
            print()
    
    print("="*70)
    print("📋 BOSS VERIFICATION URLS")
    print("="*70)
    print()
    
    for result in successful:
        if result.get("url"):
            print(f"🔗 {result['agent']}: {result['url']}")
    
    print()
    return len(successful) == len(results)

if __name__ == "__main__":
    success = asyncio.run(automate_all_agents())
    sys.exit(0 if success else 1)