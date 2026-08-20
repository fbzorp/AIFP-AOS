#!/bin/sh
set -e

# Import tasks first (sets up broker with periodiq middleware), then scheduler (registers actors)
uv run python -c "from apps.workers import tasks; from apps.workers import scheduler"

# Run periodiq
uv run periodiq apps.workers.tasks:broker
