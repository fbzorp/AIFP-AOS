#!/usr/bin/env python3
"""
Quick test to verify agents are posting successfully with clickable URLs.
Run this with: docker compose -f docker-compose.minimal.yml exec -T api uv run python scripts/test_agents_posting.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.models.base import get_sync_session
from apps.models.content_item import ContentItemModel
from sqlalchemy import select

def test_agent_posting():
    """Test that agents are posting successfully and provide clickable URLs."""
    print("="*70)
    print("🔍 AGENT POSTING VERIFICATION")
    print("="*70)
    print()
    
    with get_sync_session() as session:
        # Check recently published content
        published_content = session.execute(
            select(ContentItemModel).where(
                ContentItemModel.status == 'published'
            ).order_by(ContentItemModel.published_at.desc()).limit(10)
        ).scalars().all()
        
        print(f"📊 Found {len(published_content)} published content items:")
        print()
        
        for i, content in enumerate(published_content, 1):
            print(f"{i}. {content.author_agent}")
            print(f"   Title: {content.title[:60]}..." if len(content.title) > 60 else f"   Title: {content.title}")
            print(f"   Channel: {content.channel}")
            print(f"   Published: {content.published_at}")
            
            if content.post_url:
                print(f"   🔗 Live URL: {content.post_url}")
            elif content.post_id:
                # Generate clickable URL based on channel
                if content.channel == "moltbook":
                    url = f"https://www.moltbook.com/api/v1/posts/{content.post_id}"
                    print(f"   🔗 API URL: {url}")
                elif content.channel == "telegram":
                    url = f"https://t.me/c/{content.post_id}"
                    print(f"   🔗 Telegram URL: {url}")
                else:
                    print(f"   Post ID: {content.post_id}")
            else:
                print(f"   ⚠️  No URL available - post may have failed")
            
            print()
        
        # Check approved but unpublished content
        approved_unpublished = session.execute(
            select(ContentItemModel).where(
                ContentItemModel.status == 'approved',
                ContentItemModel.post_id.is_(None)
            ).order_by(ContentItemModel.created_at.desc()).limit(5)
        ).scalars().all()
        
        print(f"⏳ Found {len(approved_unpublished)} approved but unpublished items:")
        print()
        
        for i, content in enumerate(approved_unpublished, 1):
            print(f"{i}. {content.author_agent}: {content.title[:50]}...")
            print(f"   Created: {content.created_at}")
            print()
        
        # Summary
        total_content = session.query(ContentItemModel).count()
        published_count = session.query(ContentItemModel).filter(ContentItemModel.status == 'published').count()
        approved_count = session.query(ContentItemModel).filter(ContentItemModel.status == 'approved').count()
        
        print("="*70)
        print("📈 SUMMARY")
        print("="*70)
        print(f"Total content items: {total_content}")
        print(f"Published: {published_count}")
        print(f"Approved (awaiting publishing): {approved_count}")
        print()
        
        if published_count > 0:
            print("✅ Agents are posting successfully!")
            print("Click the URLs above to verify the posts are live.")
        else:
            print("⚠️  No published content found - agents may not be posting yet.")
        
        return published_count > 0

if __name__ == "__main__":
    success = test_agent_posting()
    sys.exit(0 if success else 1)