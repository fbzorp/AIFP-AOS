#!/bin/sh
set -e

# Import the scheduler module to register actors with periodiq
uv run python -c "from apps.workers import scheduler"

# Run periodiq
uv run periodiq apps.workers.tasks:broker
