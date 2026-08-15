#!/usr/bin/env python3
"""
Run all agents sequentially with delays to respect rate limits.
This script runs automate_single_agent.py for each agent with time gaps.
"""

import subprocess
import time
import sys

def run_agent_with_delay(agent_name, delay_seconds=30):
    """Run a single agent and wait for the specified delay."""
    print(f"🚀 Starting {agent_name}...")
    print(f"⏰ Will wait {delay_seconds} seconds after completion to respect rate limits")
    print()
    
    # Run the single agent script
    result = subprocess.run([
        "docker", "compose", "-f", "docker-compose.dev.yml", "exec", "-T", "api",
        "uv", "run", "python", "scripts/automate_single_agent.py",
        "--agent", agent_name
    ], capture_output=True, text=True)
    
    # Print output
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode == 0:
        print(f"✅ {agent_name} completed successfully")
    else:
        print(f"❌ {agent_name} failed with return code {result.returncode}")
    
    # Wait for delay if not the last agent
    if delay_seconds > 0:
        print(f"⏰ Waiting {delay_seconds} seconds to respect rate limits...")
        time.sleep(delay_seconds)
    
    return result.returncode == 0

def main():
    """Run all agents sequentially."""
    print("="*70)
    print("🚀 RUNNING ALL AGENTS SEQUENTIALLY")
    print("="*70)
    print()
    
    agents = [
        "SEO Content",
        "Founder Content", 
        "Technical Content"
    ]
    
    results = {}
    
    for i, agent in enumerate(agents):
        print(f"\n📍 Agent {i+1}/{len(agents)}: {agent}")
        print("="*70)
        
        # Calculate delay (no delay after last agent)
        delay = 30 if i < len(agents) - 1 else 0
        
        success = run_agent_with_delay(agent, delay)
        results[agent] = success
        
        print()
    
    # Summary
    print("="*70)
    print("📊 SEQUENTIAL AUTOMATION SUMMARY")
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
        print("🎉 All agents completed successfully!")
        return 0
    else:
        print("⚠️  Some agents failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())