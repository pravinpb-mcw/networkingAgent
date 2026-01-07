#!/bin/bash
echo "Starting Agent 2 - Nearest AP Analysis..."
cd "$(dirname "$0")/.."

# Load environment variables from .env
source "$(dirname "$0")/load_env.sh"

"$PYTHON_EXE" agents/agent_2_nearest_ap.py --continuous 10
