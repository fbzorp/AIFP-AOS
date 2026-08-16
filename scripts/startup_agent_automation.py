#!/usr/bin/env python3
"""
Startup script to trigger initial agent automation after stack is up.
This should be run manually after docker compose up -d to kickstart autonomous publishing.
"""

import subprocess
import time
import sys
import argparse

def run_agent_automation(agent_name, delay_seconds=10):
    """Run a single agent automation with delay."""
    print(f"🚀 Starting {agent_name} automation...")
    print(f"⏰ Waiting {delay_seconds} seconds for system to stabilize...")
    time.sleep(delay_seconds)
    
    result = subprocess.run([
        "docker", "compose", "-f", "docker-compose.dev.yml", "exec", "-T", "api",
        "uv", "run", "python", "scripts/automate_single_agent.py",
        "--agent", agent_name
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode == 0:
        print(f"✅ {agent_name} automation completed successfully")
    else:
        print(f"❌ {agent_name} automation failed with return code {result.returncode}")
    
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="Startup agent automation")
    parser.add_argument("--agents", nargs="+", default=["SEO Content", "Founder Content", "Technical Content"], 
                       help="Agents to automate (default: all)")
    parser.add_argument("--delay", type=int, default=10, help="Delay between agents in seconds")
    args = parser.parse_args()
    
    print("="*70)
    print("🚀 STARTUP AGENT AUTOMATION")
    print("="*70)
    print()
    
    results = {}
    
    for i, agent in enumerate(args.agents):
        print(f"\n📍 Agent {i+1}/{len(args.agents)}: {agent}")
        print("="*70)
        
        # Calculate delay (no delay after last agent)
        delay = args.delay if i < len(args.agents) - 1 else 0
        
        success = run_agent_automation(agent, delay)
        results[agent] = success
        
        print()
    
    # Summary
    print("="*70)
    print("📊 STARTUP AUTOMATION SUMMARY")
    print("="*70)
    print()
    
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    for agent, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {agent}")
    
    print()
    print(f"Total: {successful}/{total} agents successful")
    
    if successful == total:
        print("🎉 All agents automated successfully on startup!")
        return 0
    else:
        print("⚠️  Some agents failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())