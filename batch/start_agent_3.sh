#!/bin/bash
echo "Starting Agent 3 - Failover Coordinator..."
cd "$(dirname "$0")/.."

# Load environment variables from .env
source "$(dirname "$0")/load_env.sh"

"$PYTHON_EXE" agents/agent_3_failover_suggestion.py --continuous 10
