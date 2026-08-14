"""
Test publisher parameter fixes
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

print("Testing publisher parameter fixes...")

# Test Moltbook client initialization
try:
    from apps.integrations.moltbook.client import MoltbookClient
    client = MoltbookClient(
        agent_key="test_key",
        app_key="test_app",
        timeout=20
    )
    print("✅ MoltbookClient initialized with correct parameters")
except Exception as e:
    print(f"❌ MoltbookClient failed: {e}")

# Test X client initialization
try:
    from apps.integrations.x.client import XClient
    client = XClient(
        api_key="test_key",
        api_secret="test_secret",
        access_token="test_token",
        access_token_secret="test_secret",
        timeout=20
    )
    print("✅ XClient initialized with correct parameters")
except Exception as e:
    print(f"❌ XClient failed: {e}")

# Test Telegram client initialization
try:
    from apps.integrations.telegram.client import TelegramClient
    client = TelegramClient(
        bot_token="test_token",
        chat_id="test_chat",
        timeout=20
    )
    print("✅ TelegramClient initialized with correct parameters")
except Exception as e:
    print(f"❌ TelegramClient failed: {e}")

print("\nAll parameter fixes verified!")
