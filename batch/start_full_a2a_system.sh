#!/bin/bash
# Full system with Agent-to-Agent communication
# Equivalent to start_full_a2a_system.bat

echo "================================================================================"
echo "   STARTING FULL A2A SYSTEM"
echo "================================================================================"
echo

cd "$(dirname "$0")/.."

# Load environment variables
source "$(dirname "$0")/load_env.sh"

mkdir -p logs agent_data

echo "[1/8] Starting Phoenix Observability Server (Port 6006)..."
"$PYTHON_EXE" phoenix/server.py --auto-eval --eval-interval 10 > logs/phoenix.log 2>&1 &
PHOENIX_PID=$!

echo "[2/8] Waiting for Phoenix..."
sleep 8

echo "[3/8] Starting Auto Risk Score Updater..."
"$PYTHON_EXE" scripts/auto_risk_score_updater.py --continuous 10 > logs/risk_updater.log 2>&1 &
UPDATER_PID=$!

sleep 2

echo "[4/8] Starting Agent 1 (Risk Calculation - Port 5001) with A2A..."
"$PYTHON_EXE" agents/agent_1_risk_calculation.py --continuous 10 --enable-a2a > logs/agent1.log 2>&1 &
AGENT1_PID=$!

sleep 2

echo "[5/8] Starting Agent 2 (Nearest AP - Port 5002) with A2A..."
"$PYTHON_EXE" agents/agent_2_nearest_ap.py --continuous 10 --enable-a2a > logs/agent2.log 2>&1 &
AGENT2_PID=$!

sleep 2

echo "[6/8] Starting Agent 3 (Failover - Port 5003) with A2A..."
"$PYTHON_EXE" agents/agent_3_failover_suggestion.py --continuous 10 --enable-a2a > logs/agent3.log 2>&1 &
AGENT3_PID=$!

echo "[7/8] Starting Backend Server (Port 8000)..."
"$PYTHON_EXE" -m uvicorn dashboard.backend.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
BACKEND_PID=$!

echo "[8/8] Starting React Dashboard (Port 5173)..."
cd react_dashboard
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo
echo "================================================================================"
echo "   FULL A2A SYSTEM STARTED"
echo "================================================================================"
echo "   Agent-to-Agent communication: ENABLED"
echo "   - Phoenix: http://localhost:6006"
echo "   - Agent 1: http://localhost:5001"
echo "   - Agent 2: http://localhost:5002"
echo "   - Agent 3: http://localhost:5003"
echo "   - Backend API: http://localhost:8000"
echo "   - Dashboard: http://localhost:5173"
echo "================================================================================"
echo
echo "$PHOENIX_PID $UPDATER_PID $AGENT1_PID $AGENT2_PID $AGENT3_PID $BACKEND_PID $FRONTEND_PID" > .pids
echo "To stop: ./batch/stop_agents.sh"
echo
