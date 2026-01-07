#!/bin/bash
echo "================================================================================"
echo "   RESTARTING ALL AGENTS"
echo "================================================================================"
echo

cd "$(dirname "$0")/.."

# Stop all agents first
echo "Step 1: Stopping existing agents..."
"$(dirname "$0")/stop_agents.sh"

echo
echo "Step 2: Waiting 3 seconds..."
sleep 3

echo
echo "Step 3: Starting system..."
"$(dirname "$0")/start_system.sh"
