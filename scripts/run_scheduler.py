#!/usr/bin/env python3
"""
Entry point for the periodiq scheduler.
This script loads the scheduler module (which registers actors with periodiq) and runs periodiq.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    # Import the scheduler module to register actors with periodiq
    from apps.workers import scheduler
    
    # Import periodiq's main function and argument parser
    from periodiq import main, make_argument_parser
    
    # Set up the arguments for periodiq (only need broker since actors are registered via decorator)
    sys.argv = [
        "periodiq",
        "apps.workers.tasks:broker"
    ]
    
    # Parse arguments
    parser = make_argument_parser()
    args = parser.parse_args()
    
    # Run periodiq's main function with parsed arguments
    main(args)
