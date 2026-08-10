"""
Script to relay publication results to the Telegram channel using the Telegram Republisher agent.
"""

import asyncio
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.integrations.telegram.client import TelegramClient


async def relay_results_to_telegram():
    """Relay publication results to Telegram channel."""
    print("=" * 60)
    print("RELAYING PUBLICATION RESULTS TO TELEGRAM")
    print("=" * 60)
    
    # Load the publication log
    log_file = "/app/logs/real_publications.json"
    if not os.path.exists(log_file):
        print(f"❌ Publication log not found: {log_file}")
        return
    
    with open(log_file, 'r') as f:
        publication_log = json.load(f)
    
    # Create a summary message
    timestamp = publication_log.get("timestamp", "Unknown")
    channels = publication_log.get("channels", {})
    db_records = publication_log.get("database_records", [])
    
    message = f"""
📊 **AIFP Publication Results Report**
🕒 {timestamp}

**Channel Status:**
• **Moltbook:** {channels.get('moltbook', {}).get('status', 'N/A')}
• **Telegram:** {channels.get('telegram', {}).get('status', 'N/A')}

**Real Publications Found:** {len(db_records)}

**Recent Database Records:**
"""
    
    for record in db_records[:5]:  # Show top 5
        message += f"""
• {record.get('title', 'Unknown')} 
  - Channel: {record.get('channel', 'Unknown')}
  - Agent: {record.get('author_agent', 'Unknown')}
  - URL: {record.get('post_url', 'N/A')}
"""
    
    message += """
🤖 *AIFP Autonomous Publishing System*
✅ Telegram Republisher Agent Active
"""
    
    # Send to Telegram
    print("\nSending results to Telegram channel...")
    try:
        telegram_client = TelegramClient()
        result = await telegram_client.publish_post(text=message.strip())
        
        if result.get("dry_run"):
            print("⚠️ Telegram still in dry-run mode")
        else:
            print(f"✅ Results relayed to Telegram: {result.get('post_url')}")
        
        await telegram_client.close()
        
    except Exception as e:
        print(f"❌ Failed to relay results: {e}")
    
    print("=" * 60)
    print("TELEGRAM RELAY COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(relay_results_to_telegram())
