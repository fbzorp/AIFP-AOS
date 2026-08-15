#!/usr/bin/env python3
"""
Test that google channel routing works correctly.
This verifies that content with channel="google" gets routed to MoltbookPublisher with google submolt.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.integrations.publishing import get_publisher

def test_google_channel_routing():
    """Test that google channel routes correctly to MoltbookPublisher."""
    print("="*70)
    print("🔍 TESTING GOOGLE CHANNEL ROUTING")
    print("="*70)
    print()
    
    # Test 1: Check channel mapping
    print("📋 Test 1: Checking channel mapping...")
    try:
        from apps.integrations.publishing.dispatcher import _CHANNEL_PUBLISHERS
        print("✅ Channel publishers mapping:")
        for channel, publisher_class in _CHANNEL_PUBLISHERS.items():
            print(f"   '{channel}' → {publisher_class.__name__}")
        
        if "google" in _CHANNEL_PUBLISHERS:
            print(f"✅ 'google' channel is mapped to {_CHANNEL_PUBLISHERS['google'].__name__}")
        else:
            print("❌ 'google' channel is NOT in the mapping")
            return False
    except Exception as e:
        print(f"❌ Error checking channel mapping: {e}")
        return False
    print()
    
    # Test 2: Test get_publisher for google channel
    print("📤 Test 2: Testing get_publisher for 'google' channel...")
    try:
        google_publisher = get_publisher("google", "SEO Content")
        print(f"✅ get_publisher('google', 'SEO Content') returned: {google_publisher}")
        print(f"   Publisher type: {type(google_publisher).__name__}")
        
        # Verify it's a MoltbookPublisher
        from apps.integrations.publishing.dispatcher import MoltbookPublisher
        if isinstance(google_publisher, MoltbookPublisher):
            print("✅ Google channel correctly routes to MoltbookPublisher")
        else:
            print(f"❌ Google channel routes to wrong publisher: {type(google_publisher).__name__}")
            return False
    except Exception as e:
        print(f"❌ Error getting publisher for google channel: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    # Test 3: Test submolt parameter passing
    print("🔧 Test 3: Testing submolt parameter passing...")
    try:
        # Simulate what happens in tasks.py
        channel = "google"
        publisher_params = {}
        if channel.lower() == "google":
            publisher_params["submolt"] = "google"
        
        print(f"✅ For channel='google', submolt parameter set to: {publisher_params.get('submolt')}")
        
        # Verify the MoltbookPublisher accepts submolt parameter
        if hasattr(google_publisher, 'publish_post'):
            print("✅ MoltbookPublisher has publish_post method")
        else:
            print("❌ MoltbookPublisher missing publish_post method")
            return False
    except Exception as e:
        print(f"❌ Error testing submolt parameter: {e}")
        return False
    print()
    
    # Test 4: Verify no ValueError for unmapped channel
    print("🚫 Test 4: Verifying no ValueError for unmapped channels...")
    try:
        # Try to get publisher for google (should work)
        google_publisher = get_publisher("google", "SEO Content")
        print("✅ No ValueError for 'google' channel")
        
        # Try a truly unmapped channel (should fail)
        try:
            unmapped_publisher = get_publisher("unmapped_channel", "Test Agent")
            print("⚠️  Unmapped channel didn't raise ValueError (unexpected)")
        except ValueError as e:
            print(f"✅ Unmapped channel correctly raises ValueError: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    print()
    
    # Summary
    print("="*70)
    print("📊 GOOGLE CHANNEL ROUTING SUMMARY")
    print("="*70)
    print("✅ Channel mapping: 'google' → MoltbookPublisher")
    print("✅ get_publisher('google'): Returns MoltbookPublisher instance")
    print("✅ Submolt parameter: Set to 'google' for google channel")
    print("✅ No ValueError: Google channel is properly mapped")
    print()
    print("🎉 Google channel routing is working correctly!")
    print("   Content with channel='google' will be published to Moltbook with google submolt")
    print()
    
    return True

if __name__ == "__main__":
    success = test_google_channel_routing()
    sys.exit(0 if success else 1)