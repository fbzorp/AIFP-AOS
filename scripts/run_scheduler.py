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
    # Import the necessary modules in the correct order
    # First, set up the broker with periodiq middleware
    from apps.workers import tasks
    
    # Then import the scheduler to register actors
    from apps.workers import scheduler
    
    # Then import periodic_scheduler to define SCHEDULES
    from apps.workers import periodic_scheduler
    
    # Now run periodiq using the entrypoint directly
    # Set sys.argv for periodiq CLI
    sys.argv = [
        "periodiq",
        "apps.workers.tasks:broker",
        "apps.workers.periodic_scheduler"
    ]
    
    # Import and run periodiq's entrypoint
    from periodiq import entrypoint
    entrypoint()
