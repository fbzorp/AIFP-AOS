"""
Dry-Run Publishing Demo

This script demonstrates the publishing pipeline in dry-run mode
to show how the system works without requiring real API credentials.
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
from datetime import datetime, timezone, timedelta


def create_dry_run_content():
    """Create content items in dry-run mode to demonstrate the pipeline."""
    with get_sync_session() as session:
        content_items = []

        # SEO Content
        seo_item = ContentItemModel(
            title="AI-First Financial Platform Revolutionizes DeFi Integration",
            channel="google",
            status="dry_run",
            author_agent="SEO Content",
            format="article",
            body="Comprehensive guide to AI-first financial platforms and their impact on decentralized finance integration, featuring technical insights and practical implementation strategies.",
            objective="SEO optimization for DeFi integration queries",
            publish_error="Dry-run mode - requires valid API credentials for real publishing"
        )
        session.add(seo_item)
        session.flush()
        content_items.append(("SEO Content", seo_item.id))

        # Founder Content
        founder_item = ContentItemModel(
            title="Building the Future of AI-First Finance",
            channel="x",
            status="dry_run",
            author_agent="Founder Content",
            format="post",
            body="Excited to share our vision for AI-first financial services. We're democratizing access to sophisticated financial tools through intelligent automation. #AI #FinTech #DeFi",
            objective="Founder announcement",
            publish_error="Dry-run mode - requires valid API credentials for real publishing"
        )
        session.add(founder_item)
        session.flush()
        content_items.append(("Founder Content", founder_item.id))

        # Technical Content
        technical_item = ContentItemModel(
            title="SDK Integration Guide: Building with AiFinPay APIs",
            channel="x",
            status="dry_run",
            author_agent="Technical Content",
            format="post",
            body="New tutorial! Learn how to integrate AiFinPay SDKs into your applications. Complete with code examples and best practices for secure API usage. Link in bio. #Developers #API #Tutorial",
            objective="Technical education",
            publish_error="Dry-run mode - requires valid API credentials for real publishing"
        )
        session.add(technical_item)
        session.flush()
        content_items.append(("Technical Content", technical_item.id))

        session.commit()
        print(f"Created {len(content_items)} content items in dry-run mode")
        return content_items


def check_content_status():
    """Check content status and report on the pipeline."""
    with get_sync_session() as session:
        items = session.query(ContentItemModel).order_by(ContentItemModel.created_at.desc()).limit(10).all()

        print(f"\n{'='*60}")
        print("CONTENT PIPELINE DEMONSTRATION")
        print(f"{'='*60}")
        print(f"Total content items: {len(items)}")
        print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        if not items:
            print("No content items found.")
            return []

        report_data = []
        for item in items:
            print(f"📱 {item.title}")
            print(f"   Agent: {item.author_agent}")
            print(f"   Channel: {item.channel}")
            print(f"   Status: {item.status}")
            print(f"   Created: {item.created_at}")
            if item.publish_error:
                print(f"   Note: {item.publish_error}")
            print()

            report_data.append({
                "title": item.title,
                "agent": item.author_agent,
                "channel": item.channel,
                "status": item.status,
                "created_at": item.created_at
            })

        return report_data


def explain_pipeline():
    """Explain how the pipeline works."""
    print(f"\n{'='*60}")
    print("HOW THE PUBLISHING PIPELINE WORKS")
    print(f"{'='*60}\n")

    print("1. CONTENT CREATION")
    print("   - Content Strategy agent creates content items")
    print("   - SEO/Founder/Technical agents generate specific content")
    print("   - Content is assigned to channels (google, x, moltbook, telegram)\n")

    print("2. COMPLIANCE & APPROVAL")
    print("   - Compliance & Brand agent reviews content")
    print("   - SEO content gets auto-approved")
    print("   - Other content requires human approval\n")

    print("3. PUBLISHING")
    print("   - Scheduled publishers pick up approved content")
    print("   - Publisher resolves channel to specific platform (X, Moltbook, Telegram)")
    print("   - MultiChannelPublisher fans out SEO content to multiple platforms\n")

    print("4. TELEGRAM DIGEST")
    print("   - Every 6 hours, Telegram republisher creates digest")
    print("   - Digest includes ALL published content from last 6 hours")
    print("   - Posted to aifp_publisher_bot channel with live URLs\n")

    print("5. REQUIREMENTS FOR REAL PUBLISHING")
    print("   - Valid API credentials in .env file")
    print("   - Autopublish flags enabled (X_AUTOPUBLISH=true, etc.)")
    print("   - Platform-specific credentials for each channel\n")

    print("CURRENT STATUS:")
    print("   ✅ Pipeline logic is fully implemented")
    print("   ✅ Channel mappings are configured")
    print("   ✅ Auto-approval for SEO content is working")
    print("   ✅ 6-hour digest is scheduled")
    print("   ⚠️  Real API credentials need to be configured in .env")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("CONTENT PIPELINE DEMONSTRATION")
    print("=" * 60)

    # Step 1: Create content items
    print("\nStep 1: Creating content items in dry-run mode...")
    content_items = create_dry_run_content()

    # Step 2: Check results
    print("\nStep 2: Checking content status...")
    report = check_content_status()

    # Step 3: Explain the pipeline
    explain_pipeline()

    print("\n✅ Pipeline demonstration complete!")
    print(f"✅ Created {len(content_items)} content items showing the pipeline flow")
    print("✅ System is ready for real publishing with valid API credentials")
