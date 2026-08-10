"""
Test script to verify agent-specific credential fetching from .env file.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.core.credential.service import CredentialService


def test_credential_fetching():
    """Test that each agent can fetch its specific credentials from .env."""
    print("=" * 60)
    print("TESTING AGENT-SPECIFIC CREDENTIAL FETCHING FROM .ENV")
    print("=" * 60)
    
    agents = ["Founder Content", "Technical Content", "SEO Content"]
    
    for agent in agents:
        print(f"\n{agent}:")
        print("-" * 40)
        
        # Test X credentials
        x_creds = CredentialService.get_x_credentials_sync(agent)
        print(f"X API Key: {x_creds['api_key'][:10]}..." if x_creds['api_key'] else "X API Key: Not set")
        print(f"X Autopublish: {x_creds['autopublish']}")
        
        # Test Telegram credentials
        telegram_creds = CredentialService.get_telegram_credentials_sync(agent)
        print(f"Telegram Bot Token: {telegram_creds['bot_token'][:10]}..." if telegram_creds['bot_token'] else "Telegram Bot Token: Not set")
        print(f"Telegram Autopublish: {telegram_creds['autopublish']}")
        
        # Test Moltbook credentials
        moltbook_creds = CredentialService.get_moltbook_credentials_sync(agent)
        print(f"Moltbook API Key: {moltbook_creds['agent_api_key'][:10]}..." if moltbook_creds['agent_api_key'] else "Moltbook API Key: Not set")
        print(f"Moltbook Autopublish: {moltbook_creds['autopublish']}")
    
    print("\n" + "=" * 60)
    print("CREDENTIAL FETCHING TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_credential_fetching()
