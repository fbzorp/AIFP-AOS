"""
Publishing integration module for multi-channel content publishing.
Provides channel-agnostic dispatch to Moltbook, X/Twitter, and Telegram.
"""

from .dispatcher import get_publisher, PublisherBase

__all__ = ["get_publisher", "PublisherBase"]
