#!/bin/bash
echo "================================================================================"
echo "   STARTING COMPLETE NETWORK OBSERVABILITY SYSTEM"
echo "================================================================================"
echo

cd "$(dirname "$0")/.."

# Load environment variables from .env
source "$(dirname "$0")/load_env.sh"

# Create logs directory if it doesn't exist
mkdir -p logs

echo "[1/5] Starting Phoenix Observability Server (Port 6006)..."
"$PYTHON_EXE" phoenix/server.py --auto-eval --eval-interval 10 > logs/phoenix.log 2>&1 &
PHOENIX_PID=$!
echo "   Phoenix PID: $PHOENIX_PID"

echo "Waiting for Phoenix to become ready..."
"$PYTHON_EXE" "$(dirname "$0")/check_phoenix.py"
if [ $? -ne 0 ]; then
    echo
    echo "WARNING: Phoenix may not be ready, continuing anyway..."
    echo
fi

echo "[2/5] Waiting for Phoenix to initialize..."
sleep 5

echo "[3/5] Starting Auto Risk Score Updater (reads mock data, updates every 10s)..."
"$PYTHON_EXE" scripts/auto_risk_score_updater.py --continuous 10 > logs/risk_updater.log 2>&1 &
UPDATER_PID=$!
echo "   Risk Updater PID: $UPDATER_PID"

echo "[4/5] Starting Agent 1 (Risk Calculation - Port 5001)..."
"$PYTHON_EXE" agents/agent_1_risk_calculation.py --continuous 10 > logs/agent1.log 2>&1 &
AGENT1_PID=$!
echo "   Agent 1 PID: $AGENT1_PID"

echo "[5/5] Starting Agent 2 (Nearest AP - Port 5002)..."
"$PYTHON_EXE" agents/agent_2_nearest_ap.py --continuous 10 > logs/agent2.log 2>&1 &
AGENT2_PID=$!
echo "   Agent 2 PID: $AGENT2_PID"

echo "[6/6] Starting Agent 3 (Failover Orchestrator)..."
"$PYTHON_EXE" agents/agent_3_failover_suggestion.py --continuous 10 > logs/agent3.log 2>&1 &
AGENT3_PID=$!
echo "   Agent 3 PID: $AGENT3_PID"

echo
echo "================================================================================"
echo "   SYSTEM START INITIATED"
echo "================================================================================"
echo "   - Phoenix: http://localhost:6006"
echo "   - Risk Updater: Running (updates risk_scores.json every 10s)"
echo "   - Agent 1: http://localhost:5001"
echo "   - Agent 2: http://localhost:5002"
echo
echo "PIDs saved to .pids file for easy cleanup"
echo "$PHOENIX_PID $UPDATER_PID $AGENT1_PID $AGENT2_PID $AGENT3_PID" > .pids
echo
echo "To stop all services, run: ./batch/stop_agents.sh"
echo
