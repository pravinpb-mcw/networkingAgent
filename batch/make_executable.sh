#!/bin/bash
# Script to make all shell scripts executable
# Run this once after cloning the repository on Linux

cd "$(dirname "$0")"

echo "Making all shell scripts executable..."

chmod +x load_env.sh
chmod +x start_agent_1.sh
chmod +x start_agent_2.sh
chmod +x start_agent_3.sh
chmod +x start_phoenix.sh
chmod +x start_risk_updater.sh
chmod +x start_react_dashboard.sh
chmod +x start_system.sh
chmod +x start_complete_system.sh
chmod +x start_full_a2a_system.sh
chmod +x stop_agents.sh
chmod +x restart_agents.sh
chmod +x check_agents.sh
chmod +x test_env.sh
chmod +x make_executable.sh

echo "✓ All shell scripts are now executable"
echo
echo "You can now run:"
echo "  ./start_system.sh              - Start all agents and services"
echo "  ./start_complete_system.sh     - Start everything including dashboard"
echo "  ./start_full_a2a_system.sh     - Start with Agent-to-Agent communication"
echo "  ./start_react_dashboard.sh     - Start only the dashboard"
echo "  ./check_agents.sh              - Check status of all services"
echo "  ./stop_agents.sh               - Stop all services"
echo "  ./restart_agents.sh            - Restart all services"
echo
