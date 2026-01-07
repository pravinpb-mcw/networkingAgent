#!/bin/bash
# Check if agents are running and display their status

echo "================================================================================"
echo "   AGENT STATUS CHECK"
echo "================================================================================"
echo

check_process() {
    local name=$1
    local pattern=$2
    local pid=$(pgrep -f "$pattern" | head -1)
    
    if [ ! -z "$pid" ]; then
        echo "✓ $name is RUNNING (PID: $pid)"
        return 0
    else
        echo "✗ $name is NOT RUNNING"
        return 1
    fi
}

check_port() {
    local name=$1
    local port=$2
    
    if command -v nc &> /dev/null; then
        if nc -z localhost $port 2>/dev/null; then
            echo "   ✓ Port $port is open"
            return 0
        else
            echo "   ✗ Port $port is not responding"
            return 1
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":$port "; then
            echo "   ✓ Port $port is open"
            return 0
        else
            echo "   ✗ Port $port is not responding"
            return 1
        fi
    fi
}

echo "Checking processes..."
echo

check_process "Phoenix Server" "phoenix/server.py"
check_port "Phoenix" 6006
echo

check_process "Risk Score Updater" "auto_risk_score_updater.py"
echo

check_process "Agent 1 (Risk Calculation)" "agent_1_risk_calculation.py"
check_port "Agent 1" 5001
echo

check_process "Agent 2 (Nearest AP)" "agent_2_nearest_ap.py"
check_port "Agent 2" 5002
echo

check_process "Agent 3 (Failover)" "agent_3_failover_suggestion.py"
check_port "Agent 3" 5003
echo

check_process "Backend Server" "uvicorn.*dashboard.backend.main"
check_port "Backend" 8000
echo

check_process "React Dashboard" "vite"
check_port "Frontend" 5173
echo

echo "================================================================================"
echo "   LOG FILES"
echo "================================================================================"
if [ -d "logs" ]; then
    ls -lh logs/*.log 2>/dev/null | awk '{print $9, "("$5")"}'
else
    echo "No logs directory found"
fi

echo
echo "================================================================================"
