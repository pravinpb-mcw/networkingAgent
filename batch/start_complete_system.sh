#!/bin/bash
# Complete system startup with all services including A2A
# Equivalent to start_complete_system.bat

echo "================================================================================"
echo "   STARTING COMPLETE SYSTEM WITH A2A"
echo "================================================================================"
echo

cd "$(dirname "$0")/.."

# Load environment variables from .env
source "$(dirname "$0")/load_env.sh"

# Create logs directory if it doesn't exist
mkdir -p logs agent_data

echo "[1/7] Starting Phoenix Observability Server (Port 6006)..."
"$PYTHON_EXE" phoenix/server.py --auto-eval --eval-interval 10 > logs/phoenix.log 2>&1 &
PHOENIX_PID=$!
echo "   Phoenix PID: $PHOENIX_PID"

echo "Waiting for Phoenix to become ready..."
sleep 8

echo "[2/7] Starting Auto Risk Score Updater..."
"$PYTHON_EXE" scripts/auto_risk_score_updater.py --continuous 10 > logs/risk_updater.log 2>&1 &
UPDATER_PID=$!
echo "   Risk Updater PID: $UPDATER_PID"

echo "[3/7] Starting Agent 1 (Risk Calculation - Port 5001)..."
"$PYTHON_EXE" agents/agent_1_risk_calculation.py --continuous 10 > logs/agent1.log 2>&1 &
AGENT1_PID=$!
echo "   Agent 1 PID: $AGENT1_PID"

echo "[4/7] Starting Agent 2 (Nearest AP - Port 5002)..."
"$PYTHON_EXE" agents/agent_2_nearest_ap.py --continuous 10 > logs/agent2.log 2>&1 &
AGENT2_PID=$!
echo "   Agent 2 PID: $AGENT2_PID"

echo "[5/7] Starting Agent 3 (Failover Orchestrator - Port 5003)..."
"$PYTHON_EXE" agents/agent_3_failover_suggestion.py --continuous 10 > logs/agent3.log 2>&1 &
AGENT3_PID=$!
echo "   Agent 3 PID: $AGENT3_PID"

echo "[6/7] Starting Backend Server (Port 8000)..."
if [ -f "dashboard/backend/main.py" ]; then
    "$PYTHON_EXE" -m uvicorn dashboard.backend.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo "   ✓ Backend PID: $BACKEND_PID"
else
    echo "   ⚠ Backend not found, skipping..."
    BACKEND_PID=""
fi

echo "[7/7] Starting React Dashboard (Port 5173)..."
if [ -d "react_dashboard" ]; then
    cd react_dashboard
    
    # Check for bun or npm
    if command -v bun &> /dev/null; then
        PKG_MANAGER="bun"
    elif command -v npm &> /dev/null; then
        PKG_MANAGER="npm"
    else
        echo "   ⚠ Neither bun nor npm found, skipping frontend..."
        cd ..
        FRONTEND_PID=""
    fi
    
    if [ ! -z "$PKG_MANAGER" ]; then
        if [ ! -d "node_modules" ]; then
            echo "   Installing dependencies with $PKG_MANAGER..."
            $PKG_MANAGER install > /dev/null 2>&1
        fi
        $PKG_MANAGER run dev > ../logs/frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo "   ✓ Frontend PID: $FRONTEND_PID"
        cd ..
    fi
else
    echo "   ⚠ react_dashboard not found, skipping..."
    FRONTEND_PID=""
fi

echo
echo "================================================================================"
echo "   COMPLETE SYSTEM STARTED"
echo "================================================================================"
echo "   - Phoenix: http://localhost:6006"
echo "   - Agent 1: http://localhost:5001"
echo "   - Agent 2: http://localhost:5002"
echo "   - Agent 3: http://localhost:5003"
echo "   - Backend API: http://localhost:8000"
echo "   - Dashboard: http://localhost:5173"
echo "================================================================================"
echo
echo "Process IDs saved to .pids file"
echo "$PHOENIX_PID $UPDATER_PID $AGENT1_PID $AGENT2_PID $AGENT3_PID $BACKEND_PID $FRONTEND_PID" > .pids
echo
echo "To stop all services: ./batch/stop_agents.sh"
echo "View logs: tail -f logs/*.log"
echo
