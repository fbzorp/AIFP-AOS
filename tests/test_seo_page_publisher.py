"""Tests for SEO Page Publisher."""

import pytest
import tempfile
from pathlib import Path
from apps.integrations.publishing.seo_page_publisher import SeoPagePublisher


@pytest.mark.asyncio
async def test_seo_page_publisher_generates_html():
    """Test that SEO page publisher generates valid HTML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        publisher = SeoPagePublisher()
        publisher._output_dir = Path(tmpdir)
        publisher._base_url = "https://example.com/seo"
        publisher._initialized = True
        
        content = {
            "title": "Test SEO Article",
            "body": "<p>This is test content.</p>",
            "variants": {
                "seo_title_tag": "Test SEO Article - Complete Guide",
                "meta_description": "Learn about SEO optimization",
                "keywords": ["seo", "optimization"],
                "h1": "Test SEO Article"
            }
        }
        
        result = await publisher.publish_post(
            title="Test SEO Article",
            body="<p>This is test content.</p>",
            content_id="test-123",
            variants=content["variants"]
        )
        
        assert result["success"] is True
        assert result["post_id"] == "test-123"
        assert result["post_url"] == "https://example.com/seo/test-123.html"
        
        # Verify file was created
        html_file = Path(tmpdir) / "test-123.html"
        assert html_file.exists()
        
        # Verify HTML content
        html_content = html_file.read_text()
        assert "<!DOCTYPE html>" in html_content
        assert "Test SEO Article - Complete Guide" in html_content
        assert "Learn about SEO optimization" in html_content
        assert "<p>This is test content.</p>" in html_content


@pytest.mark.asyncio
async def test_seo_page_publisher_requires_content_id():
    """Test that SEO page publisher requires content_id."""
    with tempfile.TemporaryDirectory() as tmpdir:
        publisher = SeoPagePublisher()
        publisher._output_dir = Path(tmpdir)
        publisher._base_url = "https://example.com/seo"
        publisher._initialized = True
        
        result = await publisher.publish_post(
            title="Test",
            body="Content"
        )
        
        assert result["success"] is False
        assert "content_id required" in result["error"]


@pytest.mark.asyncio
async def test_seo_page_publisher_handles_variants():
    """Test that SEO page publisher properly handles variants."""
    with tempfile.TemporaryDirectory() as tmpdir:
        publisher = SeoPagePublisher()
        publisher._output_dir = Path(tmpdir)
        publisher._base_url = "https://example.com/seo"
        publisher._initialized = True
        
        variants = {
            "seo_title_tag": "Custom Title",
            "meta_description": "Custom description",
            "keywords": ["keyword1", "keyword2"],
            "h1": "Custom H1"
        }
        
        result = await publisher.publish_post(
            title="Original Title",
            body="Body content",
            content_id="test-456",
            variants=variants
        )
        
        assert result["success"] is True
        
        html_file = Path(tmpdir) / "test-456.html"
        html_content = html_file.read_text()
        
        # Verify variants are used in HTML
        assert "Custom Title" in html_content
        assert "Custom description" in html_content
        assert "keyword1, keyword2" in html_content
        assert "Custom H1" in html_content


def test_seo_page_publisher_sitemap_generation():
    """Test sitemap.xml generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        publisher = SeoPagePublisher()
        publisher._output_dir = Path(tmpdir)
        publisher._base_url = "https://example.com/seo"
        publisher._initialized = True
        
        # Create some test HTML files
        (Path(tmpdir) / "test1.html").write_text("<html></html>")
        (Path(tmpdir) / "test2.html").write_text("<html></html>")
        
        sitemap = publisher.generate_sitemap()
        
        assert '<?xml version="1.0"' in sitemap
        assert "https://example.com/seo/test1.html" in sitemap
        assert "https://example.com/seo/test2.html" in sitemap


def test_seo_page_publisher_robots_txt_generation():
    """Test robots.txt generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        publisher = SeoPagePublisher()
        publisher._output_dir = Path(tmpdir)
        publisher._base_url = "https://example.com/seo"
        publisher._initialized = True
        
        robots_txt = publisher.generate_robots_txt()
        
        assert "User-agent: *" in robots_txt
        assert "Allow: /blog/" in robots_txt
        assert "Disallow: /api/" in robots_txt
        assert "Sitemap: https://example.com/seo/sitemap.xml" in robots_txt
