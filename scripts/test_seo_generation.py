"""
Test script for SEO page generation in local development.
This script tests the HTML generation logic without requiring a deployed server.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.integrations.publishing.seo_page_publisher import SeoPagePublisher


async def test_seo_generation():
    """Test SEO page generation with local configuration."""
    print("Testing SEO Page Generation...")
    print("=" * 50)
    
    # Create publisher with local settings
    publisher = SeoPagePublisher()
    publisher._output_dir = Path("./seo_pages")
    publisher._base_url = "https://aifinpay.io/blog"
    publisher._initialized = True
    
    # Ensure output directory exists
    publisher._output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test content
    test_content = {
        "title": "Test SEO Article for Local Development",
        "body": "<p>This is a test article for SEO page generation.</p><p>It contains sample content to verify the HTML generation works correctly.</p>",
        "variants": {
            "seo_title_tag": "Test SEO Article - AiFinPay Guide",
            "meta_description": "Learn about AiFinPay's autonomous marketing system and SEO capabilities in this test article.",
            "keywords": ["aifinpay", "seo", "autonomous marketing", "test"],
            "h1": "Test SEO Article for Local Development"
        }
    }
    
    # Generate SEO page
    print(f"Generating SEO page for: {test_content['title']}")
    result = await publisher.publish_post(
        title=test_content["title"],
        body=test_content["body"],
        content_id="test-local-dev-001",
        variants=test_content["variants"]
    )
    
    print(f"Result: {result}")
    
    # Check generated files
    print("\n" + "=" * 50)
    print("Generated Files:")
    print("=" * 50)
    
    seo_dir = Path("./seo_pages")
    if seo_dir.exists():
        files = list(seo_dir.glob("*"))
        for file in files:
            print(f"✓ {file.name} ({file.stat().st_size} bytes)")
            
            # Show preview of key files
            if file.name == "test-local-dev-001.html":
                print(f"\nPreview of {file.name}:")
                with open(file, 'r') as f:
                    lines = f.readlines()[:10]  # First 10 lines
                    print("".join(lines))
                    print("... (truncated)")
            
            elif file.name == "sitemap.xml":
                print(f"\nContent of {file.name}:")
                with open(file, 'r') as f:
                    print(f.read())
            
            elif file.name == "robots.txt":
                print(f"\nContent of {file.name}:")
                with open(file, 'r') as f:
                    print(f.read())
    else:
        print("❌ No seo_pages directory found")
    
    print("\n" + "=" * 50)
    print("Test Complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Review generated files in ./seo_pages/")
    print("2. Open test-local-dev-001.html in a browser to verify rendering")
    print("3. Use 'python -m http.server 8080' in seo_pages/ to test locally")
    print("4. When ready for production, deploy to VPS and update SEO_PAGES_OUTPUT_DIR")


if __name__ == "__main__":
    asyncio.run(test_seo_generation())
