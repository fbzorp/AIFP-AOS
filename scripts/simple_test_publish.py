#!/usr/bin/env python3
"""
Simple test script to verify publishing without agent registry dependencies.
This bypasses the periodiq import issues.
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

async def test_simple_publish():
    """Test publishing without agent dependencies."""
    print("="*70)
    print("🚀 SIMPLE PUBLISHING TEST")
    print("="*70)
    print()
    
    with get_sync_session() as session:
        # Create test content
        content = ContentItemModel(
            title='Test Autonomous Publishing',
            body='This is a test post to verify autonomous publishing is working. #AI #DeFi #Blockchain',
            channel='moltbook',
            status='draft',
            objective='Test autonomous publishing',
            author_agent='Test System'
        )
        session.add(content)
        session.commit()
        session.refresh(content)
        print(f'✅ Created content: {content.id}')
        
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
        print(f'✅ Auto-approved content')
        
        # Try to publish directly
        try:
            from apps.workers.tasks import _perform_publish_logic
            result = await _perform_publish_logic(session, content.id, approval.id, draft_hash)
            print(f'📤 Publishing result: {result}')
            
            if result.get("status") == "published":
                print(f'✅ SUCCESS: Content published')
                if result.get("post_url"):
                    print(f'🔗 Live URL: {result.get("post_url")}')
                if result.get("post_id"):
                    print(f'📝 Post ID: {result.get("post_id")}')
                return True
            else:
                print(f'❌ FAILED: {result}')
                return False
                
        except Exception as e:
            print(f'❌ Error: {e}')
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_publish())
    sys.exit(0 if success else 1)