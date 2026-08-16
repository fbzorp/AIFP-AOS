#!/usr/bin/env python3
"""
Gather all past and present verifiable URLs for all channels.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.models.base import get_sync_session
from apps.models.content_item import ContentItemModel
from sqlalchemy import select

def gather_all_urls():
    """Gather all published content with URLs."""
    print("="*70)
    print("🔍 GATHERING ALL VERIFIABLE URLS")
    print("="*70)
    print()
    
    with get_sync_session() as session:
        # Get all published content with URLs
        published_content = session.execute(
            select(ContentItemModel).where(
                ContentItemModel.status == "published",
                ContentItemModel.post_url.isnot(None)
            ).order_by(ContentItemModel.published_at.desc())
        ).scalars().all()
        
        # Remove duplicates by post_id
        seen_post_ids = set()
        unique_content = []
        for content in published_content:
            if content.post_id not in seen_post_ids:
                seen_post_ids.add(content.post_id)
                unique_content.append(content)
        
        print(f"📊 Found {len(unique_content)} published content items with URLs:")
        print()
        
        urls_by_channel = {}
        
        for i, content in enumerate(unique_content, 1):
            channel = content.channel
            if channel not in urls_by_channel:
                urls_by_channel[channel] = []
            
            urls_by_channel[channel].append({
                "id": i,
                "agent": content.author_agent,
                "title": content.title,
                "url": content.post_url,
                "post_id": content.post_id,
                "published": content.published_at
            })
        
        # Display by channel
        for channel, items in urls_by_channel.items():
            print(f"📢 {channel.upper()} CHANNEL ({len(items)} items):")
            print("-" * 70)
            for item in items:
                print(f"{item['id']}. {item['agent']}")
                print(f"   Title: {item['title'][:60]}..." if len(item['title']) > 60 else f"   Title: {item['title']}")
                print(f"   🔗 URL: {item['url']}")
                print(f"   📝 Post ID: {item['post_id']}")
                print(f"   📅 Published: {item['published']}")
                print()
        
        # Summary
        print("="*70)
        print("📊 SUMMARY BY CHANNEL")
        print("="*70)
        print()
        
        for channel, items in urls_by_channel.items():
            print(f"{channel.upper()}: {len(items)} items")
        
        print()
        print(f"Total: {len(unique_content)} verifiable URLs")
        print()
        
        # All URLs list
        print("="*70)
        print("📋 ALL VERIFIABLE URLS")
        print("="*70)
        print()
        
        for channel, items in urls_by_channel.items():
            for item in items:
                print(f"🔗 {item['url']}")
        
        return urls_by_channel

if __name__ == "__main__":
    urls_by_channel = gather_all_urls()
    sys.exit(0 if urls_by_channel else 1)