"""
Capture real (non-dry-run) publications across all channels and log results.
This will be used to verify real publishing functionality.
"""

import asyncio
import sys
import os
import json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.integrations.telegram.client import TelegramClient
from apps.models.base import get_sync_session
from apps.models.content_item import ContentItemModel


async def capture_publication_logs():
    """Capture real publication logs for all channels."""
    print("=" * 60)
    print("CAPTURING REAL PUBLICATION LOGS")
    print("=" * 60)
    
    log_file = "/app/logs/real_publications.json"
    os.makedirs("/app/logs", exist_ok=True)
    
    publication_log = {
        "timestamp": datetime.now().isoformat(),
        "channels": {},
        "database_records": []
    }
    
    # Test Moltbook (skip due to rate limiting, check database instead)
    print("\n1. Skipping Moltbook Test (rate limited) - will check database for existing publications...")
    publication_log["channels"]["moltbook"] = {
        "status": "skipped",
        "reason": "rate_limited",
        "note": "Will check database for existing publications"
    }
    
    # Test Telegram
    print("\n2. Testing Telegram Real Publishing...")
    try:
        telegram_client = TelegramClient()
        telegram_result = await telegram_client.publish_post(
            text="Real Telegram Test - Publication Log Capture via AIFP automation"
        )
        publication_log["channels"]["telegram"] = {
            "status": "success" if not telegram_result.get("dry_run") else "dry_run",
            "post_id": telegram_result.get("post_id"),
            "post_url": telegram_result.get("post_url"),
            "dry_run": telegram_result.get("dry_run", True)
        }
        print(f"✅ Telegram: {publication_log['channels']['telegram']}")
        await telegram_client.close()
    except Exception as e:
        publication_log["channels"]["telegram"] = {
            "status": "error",
            "error": str(e)
        }
        print(f"❌ Telegram: {e}")
    
    # Check database for recent real publications
    print("\n3. Checking Database for Recent Real Publications...")
    with get_sync_session() as session:
        recent_publications = session.query(ContentItemModel).filter(
            ContentItemModel.status == "published",
            ContentItemModel.post_id.isnot(None),
            ContentItemModel.post_url.isnot(None)
        ).order_by(ContentItemModel.published_at.desc()).limit(10).all()
        
        for pub in recent_publications:
            publication_log["database_records"].append({
                "id": pub.id,
                "title": pub.title,
                "channel": pub.channel,
                "author_agent": pub.author_agent,
                "post_id": pub.post_id,
                "post_url": pub.post_url,
                "published_at": pub.published_at.isoformat() if pub.published_at else None
            })
        
        print(f"Found {len(recent_publications)} recent real publications in database")
    
    # Save log file
    with open(log_file, 'w') as f:
        json.dump(publication_log, f, indent=2)
    
    print(f"\n4. Publication log saved to: {log_file}")
    print("=" * 60)
    print("PUBLICATION LOG CAPTURE COMPLETE")
    print("=" * 60)
    
    return publication_log


if __name__ == "__main__":
    asyncio.run(capture_publication_logs())
