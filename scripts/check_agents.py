#!/usr/bin/env python3
"""
Agent Status Checker
Checks which agents are currently running by testing their ports.
"""

import socket
from typing import Dict, Tuple

def check_port(port: int) -> bool:
    """Check if a port is in use"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result == 0
    except:
        return False

def check_agent_status(port: int) -> Tuple[bool, str]:
    """Check if agent is running"""
    if check_port(port):
        return True, "Running"
    else:
        return False, "Not running"

def main():
    """Check all agent status"""
    agents = {
        "Risk Score Agent (Agent 1)": 5001,
        "Nearest AP Agent (Agent 2)": 5002,
        "Network Monitor Agent (Agent 3)": 5003
    }
    
    print("🔍 Network Observability Agent Status")
    print("=" * 50)
    
    for agent_name, port in agents.items():
        running, status = check_agent_status(port)
        emoji = "✅" if running else "❌"
        print(f"{emoji} {agent_name:30} Port {port:4} - {status}")
    
    print("\n💡 Tips:")
    print("   • Start all agents: python main.py")
    print("   • Start monitor only: python main.py --agent monitor")
    print("   • Dependencies auto-start when starting monitor agent")

if __name__ == "__main__":
    main()