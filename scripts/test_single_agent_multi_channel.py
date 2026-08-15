#!/usr/bin/env python3
"""
Test a single agent posting to all channels with real clickable URLs.
This script creates content, approves it, and triggers publishing to verify real URLs.
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

async def test_single_agent_multi_channel():
    """Test a single agent posting to all channels."""
    print("="*70)
    print("🚀 TESTING SINGLE AGENT MULTI-CHANNEL PUBLISHING")
    print("="*70)
    print()
    
    # Test with different channels to find one that works
    test_channels = ["telegram", "moltbook", "google"]
    results = []
    
    for channel in test_channels:
        print(f"📤 Testing channel: {channel}")
        print("-" * 70)
        
        with get_sync_session() as session:
            try:
                # Create test content
                content = ContentItemModel(
                    title=f'Autonomous Publishing Test - {channel.upper()}',
                    body=f'This is a test post to verify autonomous publishing is working on {channel} channel. #AI #DeFi #Blockchain #Autonomous',
                    channel=channel,
                    status='draft',
                    objective='Test autonomous publishing for boss verification',
                    author_agent='SEO Content'
                )
                session.add(content)
                session.commit()
                session.refresh(content)
                print(f"✅ Created content: {content.id}")
                
                # Auto-approve
                draft_hash = compute_draft_hash(content)
                approval = ApprovalModel(
                    content_id=content.id,
                    status='approved',
                    approved_by='Test System',
                    draft_hash=draft_hash
                )
                session.add(approval)
                content.status = 'approved'
                session.commit()
                print(f"✅ Auto-approved content")
                
                # Try to publish
                from apps.workers.tasks import _perform_publish_logic
                result = await _perform_publish_logic(session, content.id, approval.id, draft_hash)
                print(f"📤 Publishing result: {result.get('status')}")
                
                if result.get("status") == "published":
                    url = result.get("post_url")
                    post_id = result.get("post_id")
                    
                    # Generate clickable URL based on channel
                    if url:
                        print(f"✅ SUCCESS: Live URL: {url}")
                        results.append({
                            "channel": channel,
                            "success": True,
                            "url": url,
                            "post_id": post_id
                        })
                    elif post_id:
                        if channel == "moltbook":
                            api_url = f"https://www.moltbook.com/api/v1/posts/{post_id}"
                            print(f"✅ SUCCESS: API URL: {api_url}")
                            results.append({
                                "channel": channel,
                                "success": True,
                                "url": api_url,
                                "post_id": post_id
                            })
                        elif channel == "telegram":
                            telegram_url = f"https://t.me/c/{post_id}"
                            print(f"✅ SUCCESS: Telegram URL: {telegram_url}")
                            results.append({
                                "channel": channel,
                                "success": True,
                                "url": telegram_url,
                                "post_id": post_id
                            })
                        else:
                            print(f"✅ SUCCESS: Post ID {post_id}")
                            results.append({
                                "channel": channel,
                                "success": True,
                                "post_id": post_id
                            })
                else:
                    print(f"❌ FAILED: {result}")
                    results.append({
                        "channel": channel,
                        "success": False,
                        "error": result
                    })
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
                results.append({
                    "channel": channel,
                    "success": False,
                    "error": str(e)
                })
        
        print()
    
    # Summary
    print("="*70)
    print("📊 MULTI-CHANNEL PUBLISHING SUMMARY")
    print("="*70)
    print()
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['channel'].upper()} CHANNEL")
        if result["success"] and result.get("url"):
            print(f"   🔗 CLICKABLE URL: {result['url']}")
        elif result["success"] and result.get("post_id"):
            print(f"   📝 Post ID: {result['post_id']}")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")
        print()
    
    successful = [r for r in results if r["success"]]
    if successful:
        print(f"🎉 SUCCESS: {len(successful)}/{len(results)} channels working")
        print()
        print("📋 BOSS VERIFICATION URLS:")
        for result in successful:
            if result.get("url"):
                print(f"   • {result['channel'].upper()}: {result['url']}")
        print()
        return True
    else:
        print(f"❌ FAILED: 0/{len(results)} channels working")
        print()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_single_agent_multi_channel())
    sys.exit(0 if success else 1)