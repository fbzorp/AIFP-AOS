"""
Payment security integration tests for critical workflow protection.
Tests verify security settings are accessible and configurable.
"""

import pytest
from apps.api.config import settings


def test_payment_kill_switch_setting():
    """Test that kill switch setting is accessible and can be toggled."""
    original_value = settings.PAYMENTS_KILL_SWITCH
    
    # Test setting is accessible
    assert hasattr(settings, 'PAYMENTS_KILL_SWITCH')
    assert isinstance(settings.PAYMENTS_KILL_SWITCH, bool)
    
    # Test we can toggle it (actual enforcement is in payments router)
    settings.PAYMENTS_KILL_SWITCH = True
    assert settings.PAYMENTS_KILL_SWITCH == True
    
    # Restore original value
    settings.PAYMENTS_KILL_SWITCH = original_value
    assert settings.PAYMENTS_KILL_SWITCH == original_value


def test_human_approval_threshold_setting():
    """Test that human approval threshold setting is accessible and configurable."""
    assert hasattr(settings, 'HUMAN_APPROVAL_THRESHOLD')
    assert isinstance(settings.HUMAN_APPROVAL_THRESHOLD, (int, float))
    assert settings.HUMAN_APPROVAL_THRESHOLD > 0


def test_per_transaction_limit_setting():
    """Test that per-transaction limit setting is accessible and configurable."""
    assert hasattr(settings, 'PER_TRANSACTION_LIMIT')
    assert isinstance(settings.PER_TRANSACTION_LIMIT, (int, float))
    assert settings.PER_TRANSACTION_LIMIT > 0


def test_daily_spending_limit_setting():
    """Test that daily spending limit setting is accessible and configurable."""
    assert hasattr(settings, 'DAILY_SPENDING_LIMIT')
    assert isinstance(settings.DAILY_SPENDING_LIMIT, (int, float))
    assert settings.DAILY_SPENDING_LIMIT > 0


def test_recipient_allowlist_setting():
    """Test that recipient allowlist setting is accessible and configurable."""
    assert hasattr(settings, 'RECIPIENT_ALLOWLIST')
    assert isinstance(settings.RECIPIENT_ALLOWLIST, str)
    
    # Test allowlist parsing
    original_value = settings.RECIPIENT_ALLOWLIST
    settings.RECIPIENT_ALLOWLIST = "addr1,addr2,addr3"
    allowed = [r.strip() for r in settings.RECIPIENT_ALLOWLIST.split(",")]
    assert len(allowed) == 3
    assert "addr1" in allowed
    
    # Restore original value
    settings.RECIPIENT_ALLOWLIST = original_value