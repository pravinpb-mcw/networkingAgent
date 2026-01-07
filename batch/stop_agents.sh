#!/bin/bash
echo "================================================================================"
echo "   STOPPING ALL AGENTS"
echo "================================================================================"
echo

cd "$(dirname "$0")/.."

# Read PIDs from file if it exists
if [ -f ".pids" ]; then
    echo "Stopping processes from .pids file..."
    while read -r pid; do
        if [ ! -z "$pid" ]; then
            kill -15 $pid 2>/dev/null && echo "   ✓ Stopped process $pid" || echo "   ✗ Process $pid not found"
        fi
    done < <(tr ' ' '\n' < .pids)
    rm .pids
fi

# Also try to kill by name
echo
echo "Terminating agent processes by name..."
pkill -f "agent_1_risk_calculation.py" && echo "   ✓ Stopped Agent 1" || echo "   ○ Agent 1 not running"
pkill -f "agent_2_nearest_ap.py" && echo "   ✓ Stopped Agent 2" || echo "   ○ Agent 2 not running"
pkill -f "agent_3_failover_suggestion.py" && echo "   ✓ Stopped Agent 3" || echo "   ○ Agent 3 not running"
pkill -f "phoenix/server.py" && echo "   ✓ Stopped Phoenix" || echo "   ○ Phoenix not running"
pkill -f "auto_risk_score_updater.py" && echo "   ✓ Stopped Risk Updater" || echo "   ○ Risk Updater not running"

echo
echo "✓ All agent processes stopped"
echo
