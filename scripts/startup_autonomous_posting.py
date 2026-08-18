#!/usr/bin/env python3
"""
DEMO SCRIPT: Startup Autonomous Publishing Script

⚠️  WARNING: This is a DEMO script for testing purposes only.
- It creates content in PENDING_REVIEW status (requires human approval)
- It does NOT auto-approve or auto-publish content
- Set DEMO_MODE=true environment variable to run this script
- DO NOT use in production without explicit operator approval

This script triggers autonomous content generation when the machine starts.
It ensures all agents begin creating content immediately upon system startup.

Functions:
1. Triggers content generation for all major agents
2. Sets content to PENDING_REVIEW for human approval
3. Provides startup verification

Run this script when the system starts to kickstart content generation.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Safety check: require DEMO_MODE=true
if os.environ.get("DEMO_MODE") != "true":
    print("❌ ERROR: This is a demo script. Set DEMO_MODE=true environment variable to run.")
    print("⚠️  This script creates PENDING_REVIEW content only - no auto-approval.")
    sys.exit(1)

from apps.models.base import get_sync_session
from apps.models.content_item import ContentItemModel
from apps.agents.registry import get_agent
from apps.core.audit.service import record_event
from sqlalchemy import select

# Major agents to start with autonomous publishing
STARTUP_AGENTS = [
    "SEO Content",
    "Founder Content", 
    "Technical Content"
]

def generate_content_for_agent(agent_name: str):
    """Generate initial content for an agent in PENDING_REVIEW status."""
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
        
        # Set to pending_review for human approval
        with get_sync_session() as session:
            content = session.query(ContentItemModel).filter(ContentItemModel.id == content_id).first()
            if content:
                content.status = "pending_review"
                session.commit()
                print(f"✅ Content set to PENDING_REVIEW (requires human approval)")
        
        return content_id
            
    except Exception as e:
        print(f"❌ Error generating content for {agent_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def set_content_pending_review(content_id: str):
    """Set content to pending_review for human approval."""
    print(f"✅ Setting content to pending_review: {content_id}")
    
    try:
        with get_sync_session() as session:
            content = session.query(ContentItemModel).filter(ContentItemModel.id == content_id).first()
            if not content:
                print(f"❌ Content {content_id} not found")
                return False
            
            # Update content status to pending_review
            content.status = "pending_review"
            
            session.commit()
            
            # Record audit event
            record_event(session, "System", "content_pending_review", f"Content {content_id} set to pending_review for human approval", {"content_id": content_id})
            
            print(f"✅ Content {content_id} set to pending_review")
            return True
            
    except Exception as e:
        print(f"❌ Error setting content to pending_review {content_id}: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_startup_content():
    """Verify that startup content generation was successful."""
    print("\n🔍 Verifying startup content generation...")
    
    with get_sync_session() as session:
        # Check recent pending_review content
        recent_pending = session.execute(
            select(ContentItemModel).where(
                ContentItemModel.status == "pending_review"
            ).order_by(ContentItemModel.created_at.desc()).limit(10)
        ).scalars().all()
        
        print(f"📊 Found {len(recent_pending)} items in pending_review:")
        for item in recent_pending:
            print(f"  ✅ {item.author_agent}: {item.title[:50]}...")
            print(f"     Content ID: {item.id}")
        
        return len(recent_pending) > 0

def main():
    """Main startup function."""
    print("="*70)
    print("🚀 DEMO: STARTUP CONTENT GENERATION")
    print("="*70)
    print("⚠️  Content will be in PENDING_REVIEW status (requires human approval)")
    print()
    
    print("This script will:")
    print("1. Generate initial content for all major agents")
    print("2. Set content to PENDING_REVIEW for human approval")
    print("3. Verify successful content generation")
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
    
    # Step 2: Set content to pending_review
    print("Step 2: Setting content to pending_review")
    print("-"*70)
    pending_content = []
    for agent_name, content_id in generated_content:
        if set_content_pending_review(content_id):
            pending_content.append((agent_name, content_id))
        print()
    
    # Step 3: Verify content generation
    print("Step 3: Verifying content generation")
    print("-"*70)
    verification_success = verify_startup_content()
    
    # Summary
    print()
    print("="*70)
    print("📊 STARTUP CONTENT GENERATION SUMMARY")
    print("="*70)
    print(f"Agents processed: {len(STARTUP_AGENTS)}")
    print(f"Content generated: {len(generated_content)}")
    print(f"Content in pending_review: {len(pending_content)}")
    print(f"Verification: {'✅ SUCCESS' if verification_success else '❌ FAILED'}")
    print()
    
    if len(pending_content) > 0:
        print("🎉 Startup content generation completed successfully!")
        print("Content is ready for human approval via the approvals API.")
        print()
        print("To approve and publish content, use:")
        for agent_name, content_id in pending_content:
            print(f"  POST /api/v1/content/{content_id}/approve")
            print(f"  POST /api/v1/content/{content_id}/publish")
    else:
        print("⚠️  No content was generated. Check logs for errors.")
    
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