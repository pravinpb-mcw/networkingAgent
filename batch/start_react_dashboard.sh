#!/bin/bash
echo "================================================================================"
echo "   STARTING REACT DASHBOARD (v3.0)"
echo "================================================================================"
echo
cd "$(dirname "$0")/.."

# Load environment variables from .env
source "$(dirname "$0")/load_env.sh"

echo "[1/5] Clearing old agent data (keeping nearest_aps)..."
echo "[]" > agent_data/risk_scores.json
echo "[]" > agent_data/failover_suggestions.json
echo "[]" > agent_data/analysis_history.json
echo "   ✓ Data cleared"
echo

echo "[2/5] Verifying Python environment..."
if [ ! -f "$PYTHON_EXE" ]; then
    echo "Error: Python environment not found at $PYTHON_EXE"
    exit 1
fi

echo "[3/5] Checking Backend Dependencies..."
"$PYTHON_EXE" -m pip install -r dashboard/backend/requirements.txt > /dev/null

echo "[4/5] Starting Backend Server (Port 8000)..."
"$PYTHON_EXE" -m uvicorn dashboard.backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

echo "[5/5] Starting React Frontend..."
cd react_dashboard
if [ ! -d "node_modules" ]; then
    echo "   Installing Node dependencies (this may take a minute)..."
    npm install
fi

echo
echo "   Backend: http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo
echo "   Starting Vite server..."
npm run dev

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT
