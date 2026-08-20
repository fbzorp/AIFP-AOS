#!/usr/bin/env python3
"""
Entry point for the periodiq scheduler.
This script sets up the environment and runs periodiq with the proper configuration.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    # Import tasks first to set up broker with periodiq middleware
    from apps.workers import tasks
    
    # Import scheduler AFTER middleware is added to broker
    # This ensures actors can be registered with periodiq decorator
    from apps.workers import scheduler
    
    # Now run periodiq using the entrypoint directly
    # Set sys.argv for periodiq CLI - only pass broker, it will discover actors via middleware
    sys.argv = [
        "periodiq",
        "apps.workers.tasks:broker"
    ]
    
    # Import and run periodiq's entrypoint
    from periodiq import entrypoint
    entrypoint()
