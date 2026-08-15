#!/usr/bin/env python3
"""
Test publishing and provide clickable URLs for verification.
This script bypasses agent registry and periodiq issues.
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

async def test_all_agents():
    """Test publishing for all major agents."""
    print("="*70)
    print("🚀 TESTING ALL AGENTS WITH CLICKABLE URLs")
    print("="*70)
    print()
    
    test_cases = [
        {
            "title": "SEO Content Test",
            "body": "Test SEO content for autonomous publishing verification. #AI #DeFi #SEO",
            "channel": "google",
            "agent": "SEO Content"
        },
        {
            "title": "Founder Content Test", 
            "body": "Test founder content for autonomous publishing verification. #AI #FinTech #Blockchain",
            "channel": "moltbook",
            "agent": "Founder Content"
        },
        {
            "title": "Technical Content Test",
            "body": "Test technical content for autonomous publishing verification. #AI #Dev #Tutorial",
            "channel": "moltbook", 
            "agent": "Technical Content"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"🤖 Testing {test_case['agent']}...")
        
        with get_sync_session() as session:
            try:
                # Create test content
                content = ContentItemModel(
                    title=test_case['title'],
                    body=test_case['body'],
                    channel=test_case['channel'],
                    status='draft',
                    objective='Test autonomous publishing',
                    author_agent=test_case['agent']
                )
                session.add(content)
                session.commit()
                session.refresh(content)
                
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
                
                # Try to publish
                from apps.workers.tasks import _perform_publish_logic
                result = await _perform_publish_logic(session, content.id, approval.id, draft_hash)
                
                print(f"📤 Result: {result.get('status')}")
                
                if result.get("status") == "published":
                    url = result.get("post_url")
                    post_id = result.get("post_id")
                    
                    # Generate clickable URL based on channel
                    if url:
                        print(f"✅ SUCCESS: {url}")
                    elif post_id and test_case['channel'] == 'moltbook':
                        api_url = f"https://www.moltbook.com/api/v1/posts/{post_id}"
                        print(f"✅ SUCCESS: {api_url}")
                    elif post_id and test_case['channel'] == 'telegram':
                        telegram_url = f"https://t.me/c/{post_id}"
                        print(f"✅ SUCCESS: {telegram_url}")
                    else:
                        print(f"✅ SUCCESS: Post ID {post_id}")
                    
                    results.append({
                        "agent": test_case['agent'],
                        "success": True,
                        "post_id": post_id,
                        "url": url or (f"https://www.moltbook.com/api/v1/posts/{post_id}" if post_id and test_case['channel'] == 'moltbook' else None)
                    })
                else:
                    print(f"❌ FAILED: {result}")
                    results.append({
                        "agent": test_case['agent'],
                        "success": False,
                        "error": result
                    })
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                results.append({
                    "agent": test_case['agent'],
                    "success": False,
                    "error": str(e)
                })
        
        print()
    
    # Summary
    print("="*70)
    print("📊 SUMMARY")
    print("="*70)
    print()
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['agent']}")
        if result["success"] and result.get("url"):
            print(f"   🔗 {result['url']}")
        print()
    
    successful = sum(1 for r in results if r["success"])
    print(f"Total: {successful}/{len(results)} agents posting successfully")
    
    return successful == len(results)

if __name__ == "__main__":
    success = asyncio.run(test_all_agents())
    sys.exit(0 if success else 1)