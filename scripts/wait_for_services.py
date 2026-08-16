#!/usr/bin/env python3
"""
Wait for services to be healthy before running automation.
"""

import subprocess
import time
import sys

def wait_for_api():
    """Wait for API to be healthy."""
    print("⏳ Waiting for API to be healthy...")
    
    max_attempts = 30
    for i in range(max_attempts):
        try:
            result = subprocess.run([
                "docker", "compose", "-f", "docker-compose.dev.yml", "exec", "-T", "api",
                "uv", "run", "python", "-c", "print('API is ready')"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ API is ready")
                return True
        except Exception:
            pass
        
        print(f"⏳ Waiting for API... ({i+1}/{max_attempts})")
        time.sleep(2)
    
    print("❌ API did not become ready in time")
    return False

def main():
    print("="*70)
    print("🚀 WAITING FOR SERVICES")
    print("="*70)
    print()
    
    if wait_for_api():
        print()
        print("✅ All services ready, starting agent automation...")
        print()
        
        # Run the startup automation
        result = subprocess.run([
            "python", "scripts/startup_agent_automation.py"
        ])
        
        return result.returncode
    else:
        print("❌ Services not ready, aborting automation")
        return 1

if __name__ == "__main__":
    sys.exit(main())