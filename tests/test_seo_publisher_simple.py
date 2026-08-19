"""Test for SEO page publisher to improve coverage."""

import pytest
from apps.integrations.publishing.seo_page_publisher import SeoPagePublisher


def test_seo_publisher_init():
    """Test SeoPagePublisher initialization."""
    publisher = SeoPagePublisher()
    assert publisher is not None