"""
Payment security integration tests for critical workflow protection.
Tests verify security settings are accessible (full RBAC deferred to Day 14).
"""

import pytest
from apps.api.config import settings


def test_payment_kill_switch_setting():
    """Test that kill switch setting is accessible."""
    assert hasattr(settings, 'PAYMENTS_KILL_SWITCH')
    assert isinstance(settings.PAYMENTS_KILL_SWITCH, bool)


def test_human_approval_threshold_setting():
    """Test that human approval threshold setting is accessible."""
    assert hasattr(settings, 'HUMAN_APPROVAL_THRESHOLD')
    assert isinstance(settings.HUMAN_APPROVAL_THRESHOLD, (int, float))


def test_per_transaction_limit_setting():
    """Test that per-transaction limit setting is accessible."""
    assert hasattr(settings, 'PER_TRANSACTION_LIMIT')
    assert isinstance(settings.PER_TRANSACTION_LIMIT, (int, float))


def test_daily_spending_limit_setting():
    """Test that daily spending limit setting is accessible."""
    assert hasattr(settings, 'DAILY_SPENDING_LIMIT')
    assert isinstance(settings.DAILY_SPENDING_LIMIT, (int, float))


def test_recipient_allowlist_setting():
    """Test that recipient allowlist setting is accessible."""
    assert hasattr(settings, 'RECIPIENT_ALLOWLIST')
    assert isinstance(settings.RECIPIENT_ALLOWLIST, str)