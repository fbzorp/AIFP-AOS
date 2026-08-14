#!/usr/bin/env python3
"""
Startup Autonomous Publishing Script

This script triggers autonomous content generation and publishing when the machine starts.
It ensures all agents begin posting immediately upon system startup.

Functions:
1. Triggers content generation for all major agents
2. Ensures content gets auto-approved
3. Initiates publishing process
4. Provides startup verification

Run this script when the system starts to kickstart autonomous publishing.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.models.base import get_sync_session
from apps.models.content_item import ContentItemModel
from apps.models.approval import ApprovalModel
from apps.agents.registry import get_agent
from apps.core.policy.engine import PolicyEngine, compute_draft_hash
from apps.core.audit.service import record_event
from sqlalchemy import select

# Major agents to start with autonomous publishing
STARTUP_AGENTS = [
    "SEO Content",
    "Founder Content", 
    "Technical Content"
]

def generate_content_for_agent(agent_name: str):
    """Generate initial content for an agent."""
    print(f"🤖 Generating content for {agent_name}...")
    
    try:
        agent = get_agent(agent_name)
        if not agent:
            print(f"❌ Agent {agent_name} not found")
            return None
        
        # Create a content item for the agent to work on
        with get_sync_session() as session:
            content_item = ContentItemModel(
                title=f"Startup Content - {agent_name}",
                body="",
                channel="google" if agent_name == "SEO Content" else "moltbook",
                status="draft",
                objective="Generate initial content for autonomous publishing",
                target_audience="General audience",
                format="Blog post",
                cta="Learn more",
                kpi="Engagement rate",
                author_agent=agent_name
            )
            session.add(content_item)
            session.commit()
            content_id = content_item.id
            
            print(f"✅ Created content item: {content_id}")
        
        # Execute agent to generate content (outside the session to avoid binding issues)
        result = asyncio.run(agent.execute({"content_item_id": content_id}))
        print(f"📝 Agent execution result: {result}")
        
        return content_id
            
    except Exception as e:
        print(f"❌ Error generating content for {agent_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def auto_approve_content(content_id: str):
    """Auto-approve content for publishing."""
    print(f"✅ Auto-approving content: {content_id}")
    
    try:
        with get_sync_session() as session:
            content = session.query(ContentItemModel).filter(ContentItemModel.id == content_id).first()
            if not content:
                print(f"❌ Content {content_id} not found")
                return False
            
            # Compute draft hash
            draft_hash = compute_draft_hash(content)
            
            # Create approval
            approval = ApprovalModel(
                content_id=content_id,
                status="approved",
                approved_by="System Auto-Approval",
                draft_hash=draft_hash
            )
            session.add(approval)
            
            # Update content status
            content.status = "approved"
            
            session.commit()
            
            # Record audit event
            record_event(session, "System", "auto_approval", f"Auto-approved content {content_id} for startup publishing", {"content_id": content_id})
            
            print(f"✅ Content {content_id} auto-approved")
            return True
            
    except Exception as e:
        print(f"❌ Error auto-approving content {content_id}: {e}")
        import traceback
        traceback.print_exc()
        return False

def trigger_publishing(content_id: str):
    """Trigger publishing for content."""
    print(f"🚀 Triggering publishing for: {content_id}")
    
    try:
        import asyncio
        from apps.workers.tasks import _perform_publish_logic
        
        with get_sync_session() as session:
            # Get approval
            approval = session.execute(
                select(ApprovalModel).where(
                    ApprovalModel.content_id == content_id,
                    ApprovalModel.status == "approved"
                ).order_by(ApprovalModel.created_at.desc()).limit(1)
            ).scalar_one_or_none()
            
            if not approval:
                print(f"❌ No approval found for {content_id}")
                return False
            
            # Trigger publishing using the async function
            result = asyncio.run(_perform_publish_logic(session, content_id, approval.id, approval.draft_hash))
            print(f"📤 Publishing result: {result}")
            
            return result.get("status") == "published"
            
    except Exception as e:
        print(f"❌ Error triggering publishing for {content_id}: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_startup_publishing():
    """Verify that startup publishing was successful."""
    print("\n🔍 Verifying startup publishing...")
    
    with get_sync_session() as session:
        # Check recent published content
        recent_published = session.execute(
            select(ContentItemModel).where(
                ContentItemModel.status == "published",
                ContentItemModel.post_url.isnot(None)
            ).order_by(ContentItemModel.published_at.desc()).limit(10)
        ).scalars().all()
        
        print(f"📊 Found {len(recent_published)} recently published items:")
        for item in recent_published:
            print(f"  ✅ {item.author_agent}: {item.title[:50]}...")
            print(f"     URL: {item.post_url}")
        
        return len(recent_published) > 0

def main():
    """Main startup function."""
    print("="*70)
    print("🚀 STARTUP AUTONOMOUS PUBLISHING")
    print("="*70)
    print()
    
    print("This script will:")
    print("1. Generate initial content for all major agents")
    print("2. Auto-approve content for publishing")
    print("3. Trigger publishing to configured channels")
    print("4. Verify successful startup publishing")
    print()
    
    generated_content = []
    
    # Step 1: Generate content for all agents
    print("Step 1: Generating content for agents")
    print("-"*70)
    for agent_name in STARTUP_AGENTS:
        content_id = generate_content_for_agent(agent_name)
        if content_id:
            generated_content.append((agent_name, content_id))
        print()
    
    # Step 2: Auto-approve content
    print("Step 2: Auto-approving content")
    print("-"*70)
    approved_content = []
    for agent_name, content_id in generated_content:
        if auto_approve_content(content_id):
            approved_content.append((agent_name, content_id))
        print()
    
    # Step 3: Trigger publishing
    print("Step 3: Triggering publishing")
    print("-"*70)
    published_count = 0
    for agent_name, content_id in approved_content:
        if trigger_publishing(content_id):
            published_count += 1
        print()
    
    # Step 4: Verify startup publishing
    print("Step 4: Verifying startup publishing")
    print("-"*70)
    verification_success = verify_startup_publishing()
    
    # Summary
    print()
    print("="*70)
    print("📊 STARTUP PUBLISHING SUMMARY")
    print("="*70)
    print(f"Agents processed: {len(STARTUP_AGENTS)}")
    print(f"Content generated: {len(generated_content)}")
    print(f"Content approved: {len(approved_content)}")
    print(f"Content published: {published_count}")
    print(f"Verification: {'✅ SUCCESS' if verification_success else '❌ FAILED'}")
    print()
    
    if published_count > 0:
        print("🎉 Startup autonomous publishing initiated successfully!")
        print("Agents will continue publishing on their scheduled intervals.")
    else:
        print("⚠️  No content was published. Check logs for errors.")
    
    print("="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Startup process cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Startup process failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)