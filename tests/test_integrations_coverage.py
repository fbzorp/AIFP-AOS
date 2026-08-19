"""Integration tests to improve coverage of key components."""

import pytest
from apps.integrations.publishing.dispatcher import (
    MoltbookPublisher, XPublisher, TelegramPublisher, PublisherBase
)
from apps.integrations.publishing.seo_page_publisher import SeoPagePublisher


def test_publisher_base_abc():
    """Test that PublisherBase is abstract."""
    assert hasattr(PublisherBase, '__abstractmethods__')


def test_moltbook_publisher_instantiation():
    """Test MoltbookPublisher can be instantiated."""
    publisher = MoltbookPublisher()
    assert isinstance(publisher, PublisherBase)


def test_x_publisher_instantiation():
    """Test XPublisher can be instantiated."""
    publisher = XPublisher()
    assert isinstance(publisher, PublisherBase)


def test_telegram_publisher_instantiation():
    """Test TelegramPublisher can be instantiated."""
    publisher = TelegramPublisher()
    assert isinstance(publisher, PublisherBase)


def test_seo_page_publisher_instantiation():
    """Test SeoPagePublisher can be instantiated."""
    publisher = SeoPagePublisher()
    assert publisher is not None


def test_multi_channel_publisher_methods():
    """Test MultiChannelPublisher has required methods."""
    from apps.integrations.publishing.dispatcher import MultiChannelPublisher
    publisher = MultiChannelPublisher()
    assert hasattr(publisher, 'publish_post')
    assert hasattr(publisher, 'close')