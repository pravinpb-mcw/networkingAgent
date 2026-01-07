#!/bin/bash
echo "================================================================================"
echo "   AUTO RISK SCORE UPDATER"
echo "================================================================================"
echo "   Reading: mock_data/comprehensive_api_data.json"
echo "   Writing: agent_data/risk_scores.json"
echo "   Interval: 10 seconds"
echo "================================================================================"
echo

cd "$(dirname "$0")/.."

# Load environment variables from .env
source "$(dirname "$0")/load_env.sh"

"$PYTHON_EXE" scripts/auto_risk_score_updater.py --continuous 10
