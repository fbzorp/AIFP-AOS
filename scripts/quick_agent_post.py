#!/usr/bin/env python3
"""
Quick Agent Post Script - Simple and Fast

This script triggers immediate posting for one agent at a time.
Much simpler than the complex startup script.

Usage:
    python scripts/quick_agent_post.py --agent "SEO Content"
    python scripts/quick_agent_post.py --agent "Founder Content"
    python scripts/quick_agent_post.py --agent "Technical Content"
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.models.base import get_sync_session
from apps.models.content_item import ContentItemModel
from apps.models.approval import ApprovalModel
from apps.agents.registry import get_agent
from apps.core.policy.engine import compute_draft_hash
from apps.core.audit.service import record_event
from sqlalchemy import select

def trigger_agent_posting(agent_name: str):
    """Trigger immediate posting for a specific agent."""
    print(f"🚀 Triggering immediate posting for: {agent_name}")
    print("="*70)
    
    try:
        with get_sync_session() as session:
            # Find approved but unpublished content for this agent
            content = session.execute(
                select(ContentItemModel).where(
                    ContentItemModel.author_agent == agent_name,
                    ContentItemModel.status == "approved",
                    ContentItemModel.post_id.is_(None)
                ).order_by(ContentItemModel.created_at).limit(1)
            ).scalar_one_or_none()
            
            if not content:
                print(f"❌ No approved unpublished content found for {agent_name}")
                print("Creating new content instead...")
                
                # Create simple content
                import random
                from datetime import datetime
                
                topics = ["AI Finance", "DeFi Security", "Blockchain Scaling", "Smart Contracts", "Crypto Infrastructure"]
                topic = random.choice(topics)
                
                content = ContentItemModel(
                    title=f"Quick Post - {topic} ({agent_name})",
                    body=f"This is a quick autonomous post about {topic} from {agent_name}.",
                    channel="google" if agent_name == "SEO Content" else "moltbook",
                    status="draft",
                    objective="Quick autonomous posting",
                    author_agent=agent_name
                )
                session.add(content)
                session.commit()
                session.refresh(content)
                
                # Generate content using agent
                agent = get_agent(agent_name)
                if agent:
                    result = __import__('asyncio').run(agent.execute({"content_item_id": content.id}))
                    print(f"📝 Agent generated content: {result}")
                
                # Auto-approve
                draft_hash = compute_draft_hash(content)
                approval = ApprovalModel(
                    content_id=content.id,
                    status="approved",
                    approved_by="System Quick-Post",
                    draft_hash=draft_hash
                )
                session.add(approval)
                content.status = "approved"
                session.commit()
                
                print(f"✅ Created and auto-approved content: {content.id}")
            
            # Trigger publishing
            import asyncio
            from apps.workers.tasks import _perform_publish_logic
            
            # Get approval
            approval = session.execute(
                select(ApprovalModel).where(
                    ApprovalModel.content_id == content.id,
                    ApprovalModel.status == "approved"
                ).order_by(ApprovalModel.created_at.desc()).limit(1)
            ).scalar_one_or_none()
            
            if approval:
                print(f"🚀 Publishing content: {content.id}")
                result = asyncio.run(_perform_publish_logic(session, content.id, approval.id, approval.draft_hash))
                print(f"📤 Result: {result}")
                
                # Check result
                if result.get("status") == "published":
                    print(f"✅ SUCCESS: Content published")
                    if result.get("post_url"):
                        print(f"🔗 Live URL: {result.get('post_url')}")
                    if result.get("post_id"):
                        print(f"📝 Post ID: {result.get('post_id')}")
                    return True
                else:
                    print(f"❌ FAILED: {result}")
                    return False
            else:
                print(f"❌ No approval found")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description="Quick agent posting")
    parser.add_argument("--agent", required=True, help="Agent name (e.g., 'SEO Content')")
    args = parser.parse_args()
    
    success = trigger_agent_posting(args.agent)
    
    if success:
        print("\n🎉 Agent posting completed successfully!")
    else:
        print("\n⚠️  Agent posting failed")
        sys.exit(1)

if __name__ == "__main__":
    main()