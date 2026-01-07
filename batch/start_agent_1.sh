#!/bin/bash
echo "Starting Agent 1 - Risk Calculation..."
cd "$(dirname "$0")/.."

# Load environment variables from .env
source "$(dirname "$0")/load_env.sh"

"$PYTHON_EXE" agents/agent_1_risk_calculation.py --continuous 10
