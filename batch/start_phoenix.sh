#!/bin/bash
# Start Phoenix Observability Server with Auto-Evaluation
# Usage: ./start_phoenix.sh [--auto-eval] [--eval-interval 30]

cd "$(dirname "$0")/.."

# Load environment variables from .env
source "$(dirname "$0")/load_env.sh"

"$PYTHON_EXE" phoenix/server.py --auto-eval --eval-interval 10
