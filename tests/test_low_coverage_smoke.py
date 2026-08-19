"""Simple smoke tests for low-coverage modules."""

import pytest
from apps.core.news_fetcher import NewsFetcher
from apps.core.credential.service import CredentialService
from apps.agents.telegram_republisher import TelegramRepublisherAgent


def test_news_fetcher_smoke():
    """Test NewsFetcher initialization."""
    fetcher = NewsFetcher()
    assert fetcher is not None


def test_credential_service_smoke():
    """Test CredentialService initialization."""
    service = CredentialService()
    assert service is not None


def test_telegram_republisher_smoke():
    """Test TelegramRepublisherAgent initialization."""
    agent = TelegramRepublisherAgent()
    assert agent is not None


def test_telegram_republisher_get_capabilities():
    """Test TelegramRepublisherAgent get_capabilities."""
    agent = TelegramRepublisherAgent()
    capabilities = agent.get_capabilities()
    assert capabilities is not None