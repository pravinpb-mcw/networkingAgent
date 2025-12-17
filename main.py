#!/usr/bin/env python3
"""
Network Observability Agent System
Professional network monitoring with AI-powered risk assessment and failover recommendations.

This system provides enterprise-grade network monitoring with three specialized agents:
- Agent 1: Risk Score Calculation (monitors all APs for performance degradation)
- Agent 2: Nearest AP Recommendation (provides ranked failover candidates)  
- Agent 3: Network Monitoring & Analysis (generates professional reports)

Usage:
    python main.py                    # Start all agents with default configuration
    python main.py --agent risk       # Start only Risk Score Agent
    python main.py --agent nearest    # Start only Nearest AP Agent  
    python main.py --agent monitor    # Start only Network Monitoring Agent
    python main.py --scenario healthy # Run healthy scenario first
    python main.py --help            # Show all options
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "agents"))
sys.path.append(str(project_root / "core"))
sys.path.append(str(project_root / "server"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("network-observability")


async def run_risk_agent():
    """Start Risk Score Agent (Agent 1)"""
    from agents.risk_score_agent import RiskScoreCalculationAgent
    agent = RiskScoreCalculationAgent()
    await agent.initialize()
    await agent.continuous_calculation()


async def run_nearest_ap_agent():
    """Start Nearest AP Agent (Agent 2)"""
    from agents.nearest_ap_agent import NearestAPRecommendationAgent
    agent = NearestAPRecommendationAgent()
    await agent.initialize()
    await agent.continuous_calculation()


async def run_monitoring_agent():
    """Start Network Monitoring Agent (Agent 3)"""
    from agents.network_monitoring_agent import NetworkMonitoringAgent
    agent = NetworkMonitoringAgent()
    await agent.initialize()
    await agent.continuous_monitoring()


async def run_scenario(scenario_name: str):
    """Run a test scenario"""
    scenario_map = {
        "healthy": "scenarios.healthy",
        "partial": "scenarios.partial_degrade",
        "further": "scenarios.further_degrade", 
        "failure": "scenarios.full_failure"
    }
    
    if scenario_name not in scenario_map:
        logger.error(f"Unknown scenario: {scenario_name}")
        logger.info(f"Available scenarios: {', '.join(scenario_map.keys())}")
        return
    
    module_name = scenario_map[scenario_name]
    module = __import__(module_name, fromlist=['main'])
    await module.main()


async def run_all_agents():
    """Start all agents concurrently"""
    logger.info("🚀 Starting Network Observability Agent System...")
    logger.info("=" * 60)
    
    tasks = [
        asyncio.create_task(run_risk_agent()),
        asyncio.create_task(run_nearest_ap_agent()),
        asyncio.create_task(run_monitoring_agent())
    ]
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("\n⚠️ System shutdown requested")
        for task in tasks:
            task.cancel()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Network Observability Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--agent",
        choices=["risk", "nearest", "monitor", "all"],
        default="all",
        help="Which agent to start (default: all)"
    )
    
    parser.add_argument(
        "--scenario", 
        choices=["healthy", "partial", "further", "failure"],
        help="Run a test scenario before starting agents"
    )
    
    parser.add_argument(
        "--mock-server",
        action="store_true",
        help="Start mock Meraki server first"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mock_server:
            logger.info("🔧 Starting mock Meraki server...")
            import subprocess
            subprocess.Popen([sys.executable, "server/mock_server.py"])
            import time
            time.sleep(3)
        
        if args.scenario:
            logger.info(f"🎭 Running scenario: {args.scenario}")
            asyncio.run(run_scenario(args.scenario))
            logger.info("✅ Scenario complete. Starting agents...")
        
        if args.agent == "risk":
            asyncio.run(run_risk_agent())
        elif args.agent == "nearest":
            asyncio.run(run_nearest_ap_agent())
        elif args.agent == "monitor":
            logger.info("🔍 Starting Network Monitoring Agent (Agent 3)")
            logger.info("   Dependencies: Will auto-start Risk Score Agent & Nearest AP Agent if not running")
            asyncio.run(run_monitoring_agent())
        else:
            asyncio.run(run_all_agents())
            
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()