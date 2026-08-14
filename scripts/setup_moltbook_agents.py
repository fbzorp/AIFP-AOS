#!/usr/bin/env python3
"""
Moltbook Agent Credential Setup Script

This script helps you configure Moltbook credentials for your most important social agents.
It will:
1. Show current credential configuration
2. Guide you through setting up agent-specific credentials
3. Test the credentials once configured

IMPORTANT: Moltbook credentials use this format:
- Agent-specific: {AGENT_NAME}_MOLTBOOK_AGENT_API_KEY and {AGENT_NAME}_MOLTBOOK_APP_KEY
- Global fallback: MOLTBOOK_AGENT_API_KEY and MOLTBOOK_APP_KEY
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.agents.registry import list_agents

# Most important social agents for Moltbook
IMPORTANT_SOCIAL_AGENTS = [
    "SEO Content",
    "Founder Content", 
    "Technical Content",
    "Social Publishing Agent",
    "Community Engagement Agent"
]

def get_env_file_path():
    """Get the .env file path."""
    env_path = project_root / ".env"
    if not env_path.exists():
        env_path = project_root / ".env.example"
    return env_path

def load_current_credentials():
    """Load current Moltbook credentials from .env."""
    env_path = get_env_file_path()
    credentials = {}
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    credentials[key.strip()] = value.strip()
    
    return credentials

def agent_to_env_prefix(agent_name):
    """Convert agent name to environment variable prefix."""
    return agent_name.upper().replace(" ", "_")

def show_current_config():
    """Show current Moltbook credential configuration."""
    print("="*70)
    print("CURRENT MOLTBOOK CREDENTIAL CONFIGURATION")
    print("="*70)
    
    credentials = load_current_credentials()
    
    # Show global credentials
    print("\n📋 GLOBAL CREDENTIALS:")
    print(f"  MOLTBOOK_AGENT_API_KEY: {credentials.get('MOLTBOOK_AGENT_API_KEY', 'NOT SET')[:20]}..." if credentials.get('MOLTBOOK_AGENT_API_KEY') else "  MOLTBOOK_AGENT_API_KEY: NOT SET")
    print(f"  MOLTBOOK_APP_KEY: {credentials.get('MOLTBOOK_APP_KEY', 'NOT SET')[:20]}..." if credentials.get('MOLTBOOK_APP_KEY') else "  MOLTBOOK_APP_KEY: NOT SET")
    print(f"  MOLTBOOK_AUTOPUBLISH: {credentials.get('MOLTBOOK_AUTOPUBLISH', 'NOT SET')}")
    
    # Show agent-specific credentials
    print("\n🤖 AGENT-SPECIFIC CREDENTIALS:")
    for agent_name in IMPORTANT_SOCIAL_AGENTS:
        prefix = agent_to_env_prefix(agent_name)
        agent_key = credentials.get(f"{prefix}_MOLTBOOK_AGENT_API_KEY", "NOT SET")
        app_key = credentials.get(f"{prefix}_MOLTBOOK_APP_KEY", "NOT SET")
        
        print(f"\n  {agent_name}:")
        print(f"    {prefix}_MOLTBOOK_AGENT_API_KEY: {agent_key[:20]}..." if agent_key != "NOT SET" else f"    {prefix}_MOLTBOOK_AGENT_API_KEY: NOT SET")
        print(f"    {prefix}_MOLTBOOK_APP_KEY: {app_key[:20]}..." if app_key != "NOT SET" else f"    {prefix}_MOLTBOOK_APP_KEY: NOT SET")
    
    print("\n" + "="*70)

def setup_agent_credentials(agent_name):
    """Set up Moltbook credentials for a specific agent."""
    print(f"\n🔧 Setting up Moltbook credentials for: {agent_name}")
    print("-" * 50)
    
    prefix = agent_to_env_prefix(agent_name)
    
    print(f"\nYou'll need your Moltbook credentials for this agent.")
    print("If you don't have them, get them from: https://www.moltbook.com/developers")
    print()
    
    agent_api_key = input(f"Enter {prefix}_MOLTBOOK_AGENT_API_KEY: ").strip()
    if not agent_api_key:
        print("❌ Agent API key is required. Skipping this agent.")
        return False
    
    app_key = input(f"Enter {prefix}_MOLTBOOK_APP_KEY: ").strip()
    if not app_key:
        print("❌ App key is required. Skipping this agent.")
        return False
    
    autopublish = input(f"Enable autopublish for {agent_name}? (yes/no, default: yes): ").strip().lower()
    autopublish = "true" if autopublish in ["", "yes", "y"] else "false"
    
    # Add to .env file
    env_path = get_env_file_path()
    new_lines = []
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            existing_lines = f.readlines()
            
        # Filter out existing credentials for this agent
        skip_next = False
        for i, line in enumerate(existing_lines):
            line_stripped = line.strip()
            if line_stripped.startswith(f"{prefix}_MOLTBOOK_"):
                skip_next = False
                continue
            new_lines.append(line)
    
    # Add new credentials
    new_lines.append(f"\n# {agent_name} Moltbook Credentials\n")
    new_lines.append(f"{prefix}_MOLTBOOK_AGENT_API_KEY={agent_api_key}\n")
    new_lines.append(f"{prefix}_MOLTBOOK_APP_KEY={app_key}\n")
    new_lines.append(f"{prefix}_MOLTBOOK_AUTOPUBLISH={autopublish}\n")
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"✅ Credentials added to .env for {agent_name}")
    return True

def interactive_setup():
    """Interactive setup for Moltbook agent credentials."""
    print("🚀 MOLTBOOK AGENT CREDENTIAL SETUP")
    print("="*70)
    print("\nThis script will help you configure Moltbook credentials for your")
    print("most important social agents. You can choose which agents to configure.")
    print()
    
    # Show current configuration
    show_current_config()
    
    print("\n📝 AGENTS AVAILABLE FOR CONFIGURATION:")
    for i, agent in enumerate(IMPORTANT_SOCIAL_AGENTS, 1):
        print(f"  {i}. {agent}")
    
    print("\nWhich agents would you like to configure?")
    print("Enter agent numbers separated by commas (e.g., '1,3,5') or 'all' for all agents:")
    
    choice = input("> ").strip().lower()
    
    agents_to_configure = []
    if choice == "all":
        agents_to_configure = IMPORTANT_SOCIAL_AGENTS
    else:
        try:
            indices = [int(x.strip()) for x in choice.split(",")]
            for idx in indices:
                if 1 <= idx <= len(IMPORTANT_SOCIAL_AGENTS):
                    agents_to_configure.append(IMPORTANT_SOCIAL_AGENTS[idx - 1])
        except ValueError:
            print("❌ Invalid input. Please enter numbers separated by commas.")
            return
    
    if not agents_to_configure:
        print("❌ No agents selected. Exiting.")
        return
    
    print(f"\n🔧 Will configure {len(agents_to_configure)} agent(s): {', '.join(agents_to_configure)}")
    confirm = input("Proceed? (yes/no): ").strip().lower()
    
    if confirm not in ["yes", "y"]:
        print("❌ Setup cancelled.")
        return
    
    # Configure each agent
    success_count = 0
    for agent_name in agents_to_configure:
        if setup_agent_credentials(agent_name):
            success_count += 1
    
    print("\n" + "="*70)
    print(f"✅ SETUP COMPLETE: {success_count}/{len(agents_to_configure)} agents configured")
    print("="*70)
    
    print("\n📋 NEXT STEPS:")
    print("1. Review your .env file to confirm credentials are correct")
    print("2. Restart your Docker containers to load new credentials:")
    print("   docker compose -f docker-compose.dev.yml restart")
    print("3. Run the credential verification script to test:")
    print("   python scripts/verify_moltbook_credentials.py")
    print("4. Your agents will now use these credentials for Moltbook publishing")

def main():
    """Main entry point."""
    try:
        interactive_setup()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()