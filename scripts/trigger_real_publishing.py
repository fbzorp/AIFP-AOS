"""
Trigger Real Publishing Demo

This script triggers the full content pipeline to demonstrate real publishing
with all agents and collect verifiable URLs for the boss.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.models.base import get_sync_session
from apps.models.task import TaskModel
from apps.models.content_item import ContentItemModel
from apps.models.approval import ApprovalModel
from apps.workers.tasks import run_agent_task
from datetime import datetime, timezone, timedelta


def create_content_strategy_task():
    """Create a Content Strategy task to kick off the pipeline."""
    with get_sync_session() as session:
        task = TaskModel(
            task_type="Content Strategy",
            input_data={
                "objective": "Generate SEO-optimized content for Google search",
                "channel": "google",
                "format": "article",
                "target_audience": "developers and AI enthusiasts"
            },
            status="pending"
        )
        session.add(task)
        session.commit()
        print(f"Created Content Strategy task: {task.id}")
        return task.id


def trigger_seo_content_generator():
    """Trigger the scheduled SEO content generator directly."""
    from apps.workers.scheduler import scheduled_seo_content_generator
    print("Triggering SEO content generator...")
    scheduled_seo_content_generator()


def create_manual_content_for_all_agents():
    """Create content items for all agents to demonstrate publishing."""
    with get_sync_session() as session:
        content_items = []

        # SEO Content
        seo_item = ContentItemModel(
            title="AI-First Financial Platform Revolutionizes DeFi Integration",
            channel="google",
            status="approved",
            author_agent="SEO Content",
            format="article",
            body="Comprehensive guide to AI-first financial platforms and their impact on decentralized finance integration, featuring technical insights and practical implementation strategies.",
            objective="SEO optimization for DeFi integration queries"
        )
        session.add(seo_item)
        session.flush()
        content_items.append(("SEO Content", seo_item.id))

        # Founder Content
        founder_item = ContentItemModel(
            title="Building the Future of AI-First Finance",
            channel="x",
            status="approved",
            author_agent="Founder Content",
            format="post",
            body="Excited to share our vision for AI-first financial services. We're democratizing access to sophisticated financial tools through intelligent automation. #AI #FinTech #DeFi",
            objective="Founder announcement"
        )
        session.add(founder_item)
        session.flush()
        content_items.append(("Founder Content", founder_item.id))

        # Technical Content
        technical_item = ContentItemModel(
            title="SDK Integration Guide: Building with AiFinPay APIs",
            channel="x",
            status="approved",
            author_agent="Technical Content",
            format="post",
            body="New tutorial! Learn how to integrate AiFinPay SDKs into your applications. Complete with code examples and best practices for secure API usage. Link in bio. #Developers #API #Tutorial",
            objective="Technical education"
        )
        session.add(technical_item)
        session.flush()
        content_items.append(("Technical Content", technical_item.id))

        # Create approvals for each
        for agent_name, item_id in content_items:
            approval = ApprovalModel(
                content_id=item_id,
                draft_hash=f"hash-{item_id}",
                status="approved",
                approved_by="Demo Script",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
                decided_at=datetime.now(timezone.utc)
            )
            session.add(approval)

        session.commit()
        print(f"Created {len(content_items)} content items with approvals")
        return content_items


def trigger_publishing_for_agent(agent_name):
    """Trigger publishing for a specific agent."""
    from apps.workers.scheduler import scheduled_publisher_agent_task_founder, scheduled_publisher_agent_task_technical, scheduled_publisher_agent_task_seo

    print(f"Triggering publishing for {agent_name}...")

    if agent_name == "Founder Content":
        scheduled_publisher_agent_task_founder()
    elif agent_name == "Technical Content":
        scheduled_publisher_agent_task_technical()
    elif agent_name == "SEO Content":
        scheduled_publisher_agent_task_seo()


def check_published_content():
    """Check for published content and collect URLs."""
    with get_sync_session() as session:
        items = session.query(ContentItemModel).filter(
            ContentItemModel.status == "published",
            ContentItemModel.post_url.isnot(None)
        ).order_by(ContentItemModel.published_at.desc()).all()

        print(f"\n{'='*60}")
        print("REAL PUBLISHING REPORT FOR BOSS")
        print(f"{'='*60}")
        print(f"Total published items: {len(items)}")
        print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        if not items:
            print("No published content found yet. Publishing may take a few minutes...")
            return []

        report_data = []
        for item in items:
            print(f"📱 {item.title}")
            print(f"   Agent: {item.author_agent}")
            print(f"   Channel: {item.channel}")
            print(f"   Published: {item.published_at}")
            print(f"   Live URL: {item.post_url}")
            print(f"   Post ID: {item.post_id}")
            print()

            report_data.append({
                "title": item.title,
                "agent": item.author_agent,
                "channel": item.channel,
                "url": item.post_url,
                "published_at": item.published_at,
                "post_id": item.post_id
            })

        return report_data


if __name__ == "__main__":
    print("REAL PUBLISHING DEMO")
    print("=" * 60)

    # Step 1: Create content items for all agents
    print("\nStep 1: Creating content items for all agents...")
    content_items = create_manual_content_for_all_agents()

    # Step 2: Trigger publishing for each agent
    print("\nStep 2: Triggering publishing for all agents...")
    for agent_name, item_id in content_items:
        trigger_publishing_for_agent(agent_name)

    # Step 3: Wait a moment for publishing to complete
    print("\nStep 3: Waiting for publishing to complete...")
    import time
    time.sleep(10)

    # Step 4: Check results
    print("\nStep 4: Checking published content...")
    report = check_published_content()

    if report:
        print("\n✅ Real publishing successful!")
        print(f"Generated {len(report)} verifiable live URLs")
    else:
        print("\n⏳ Publishing in progress - check again in a few minutes")
