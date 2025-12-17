#!/usr/bin/env python3
"""
Multi-Agent Runner with A2A Support
Runs all three agents in parallel with optional A2A inter-agent communication:
- Agent 1: Risk Score Calculation (every 10s) - A2A Server on port 5001
- Agent 2: Nearest AP Recommendation (every 30s) - A2A Server on port 5002
- Agent 3: Network Monitoring (every 15s) - A2A Client

Usage:
    python run_all_agents.py                     - Run all agents with defaults
    python run_all_agents.py --risk-interval 10  - Set risk calculation interval
    python run_all_agents.py --topology-interval 30 - Set topology interval
    python run_all_agents.py --monitor-interval 15  - Set monitoring interval
    python run_all_agents.py --enable-a2a        - Enable A2A communication (default)
    python run_all_agents.py --no-a2a            - Disable A2A communication
"""

import asyncio
import argparse
import logging
import signal
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("multi-agent-runner")

# Import agents
from risk_score_agent import RiskScoreCalculationAgent
from nearest_ap_agent import NearestAPRecommendationAgent
from network_monitoring_agent import NetworkMonitoringAgent

# Import A2A server start functions
try:
    from risk_score_agent import start_a2a_server as start_risk_a2a
    from nearest_ap_agent import start_a2a_server as start_nearest_a2a
    A2A_AVAILABLE = True
except ImportError:
    A2A_AVAILABLE = False
    logger.warning("A2A server functions not available")


class MultiAgentRunner:
    """Runs all three agents in parallel with A2A support"""
    
    def __init__(
        self,
        risk_interval: int = 10,
        topology_interval: int = 30,
        monitor_interval: int = 15,
        alert_threshold: float = 40.0,
        enable_a2a: bool = True,
        risk_a2a_port: int = 5001,
        nearest_ap_a2a_port: int = 5002
    ):
        self.risk_interval = risk_interval
        self.topology_interval = topology_interval
        self.monitor_interval = monitor_interval
        self.alert_threshold = alert_threshold
        
        # A2A configuration
        self.enable_a2a = enable_a2a and A2A_AVAILABLE
        self.risk_a2a_port = risk_a2a_port
        self.nearest_ap_a2a_port = nearest_ap_a2a_port
        
        self.agents = {}
        self.tasks = []
        self.running = False
    
    async def start_a2a_servers(self):
        """Start A2A servers for Agent 1 and Agent 2"""
        if not self.enable_a2a:
            logger.info("A2A servers disabled")
            return
        
        logger.info("\n🌐 Starting A2A Servers for inter-agent communication...")
        
        try:
            # Start Risk Score Agent A2A Server (Agent 1)
            logger.info(f"   Starting Risk Score A2A Server on port {self.risk_a2a_port}...")
            start_risk_a2a(port=self.risk_a2a_port)
            
            # Start Nearest AP Agent A2A Server (Agent 2)
            logger.info(f"   Starting Nearest AP A2A Server on port {self.nearest_ap_a2a_port}...")
            start_nearest_a2a(port=self.nearest_ap_a2a_port)
            
            # Wait for servers to start
            await asyncio.sleep(2)
            
            logger.info("✅ A2A Servers started successfully!")
            logger.info(f"   - Risk Score Agent:  http://localhost:{self.risk_a2a_port}")
            logger.info(f"   - Nearest AP Agent:  http://localhost:{self.nearest_ap_a2a_port}")
            
        except Exception as e:
            logger.error(f"Failed to start A2A servers: {e}")
            logger.warning("Continuing without A2A...")
            self.enable_a2a = False
    
    async def initialize_agents(self) -> bool:
        """Initialize all three agents"""
        logger.info("="*70)
        logger.info("Initializing Multi-Agent System")
        logger.info("="*70)
        
        # Initialize Agent 1 - Risk Score
        logger.info("\n📊 Initializing Agent 1: Risk Score Calculation...")
        self.agents["risk"] = RiskScoreCalculationAgent(
            calculation_interval=self.risk_interval
        )
        if not await self.agents["risk"].initialize():
            logger.error("Failed to initialize Risk Score Agent")
            return False
        logger.info("✅ Agent 1 ready")
        
        # Initialize Agent 2 - Nearest AP
        logger.info("\n🗺️ Initializing Agent 2: Nearest AP Recommendation...")
        self.agents["topology"] = NearestAPRecommendationAgent(
            calculation_interval=self.topology_interval
        )
        if not await self.agents["topology"].initialize():
            logger.error("Failed to initialize Nearest AP Agent")
            return False
        logger.info("✅ Agent 2 ready")
        
        # Initialize Agent 3 - Network Monitoring
        logger.info("\n🔍 Initializing Agent 3: Network Monitoring...")
        self.agents["monitor"] = NetworkMonitoringAgent(
            check_interval=self.monitor_interval,
            alert_threshold=self.alert_threshold,
            enable_a2a=self.enable_a2a,
            risk_agent_port=self.risk_a2a_port,
            nearest_ap_agent_port=self.nearest_ap_a2a_port
        )
        if not await self.agents["monitor"].initialize():
            logger.error("Failed to initialize Network Monitoring Agent")
            return False
        logger.info("✅ Agent 3 ready")
        
        logger.info("\n" + "="*70)
        logger.info("All agents initialized successfully!")
        logger.info("="*70)
        
        return True
    
    async def run_risk_agent(self):
        """Run the risk score agent loop"""
        agent = self.agents["risk"]
        iteration = 0
        
        while self.running:
            try:
                iteration += 1
                logger.info(f"\n[RISK AGENT] Iteration #{iteration}")
                result = await agent.calculate_risk_scores()
                
                if result["success"]:
                    # Print summary only
                    response = result["response"]
                    summary = response[:300] + "..." if len(response) > 300 else response
                    logger.info(f"[RISK AGENT] Complete - {summary}")
                else:
                    logger.error(f"[RISK AGENT] Failed: {result.get('error')}")
                
                await asyncio.sleep(self.risk_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[RISK AGENT] Error: {e}")
                await asyncio.sleep(5)
    
    async def run_topology_agent(self):
        """Run the nearest AP agent loop"""
        agent = self.agents["topology"]
        iteration = 0
        
        while self.running:
            try:
                iteration += 1
                logger.info(f"\n[TOPOLOGY AGENT] Iteration #{iteration}")
                result = await agent.calculate_nearest_aps()
                
                if result["success"]:
                    response = result["response"]
                    summary = response[:300] + "..." if len(response) > 300 else response
                    logger.info(f"[TOPOLOGY AGENT] Complete - {summary}")
                else:
                    logger.error(f"[TOPOLOGY AGENT] Failed: {result.get('error')}")
                
                await asyncio.sleep(self.topology_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[TOPOLOGY AGENT] Error: {e}")
                await asyncio.sleep(5)
    
    async def run_monitoring_agent(self):
        """Run the network monitoring agent loop"""
        agent = self.agents["monitor"]
        iteration = 0
        
        # Wait a bit for other agents to populate data first
        await asyncio.sleep(5)
        
        while self.running:
            try:
                iteration += 1
                logger.info(f"\n[MONITOR AGENT] Iteration #{iteration}")
                result = await agent.run_monitoring_check()
                
                if result["success"]:
                    response = result["response"]
                    # Show more of the monitoring output since it's the main report
                    summary = response[:500] + "..." if len(response) > 500 else response
                    logger.info(f"[MONITOR AGENT] Report:\n{summary}")
                else:
                    logger.error(f"[MONITOR AGENT] Failed: {result.get('error')}")
                
                await asyncio.sleep(self.monitor_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[MONITOR AGENT] Error: {e}")
                await asyncio.sleep(5)
    
    async def run_all(self):
        """Run all agents concurrently with A2A support"""
        self.running = True
        
        # Start A2A servers first if enabled
        if self.enable_a2a:
            await self.start_a2a_servers()
        
        logger.info("\n" + "="*70)
        logger.info("STARTING MULTI-AGENT SYSTEM")
        logger.info(f"  Agent 1 (Risk Score):    Every {self.risk_interval}s")
        logger.info(f"  Agent 2 (Nearest AP):    Every {self.topology_interval}s")
        logger.info(f"  Agent 3 (Monitoring):    Every {self.monitor_interval}s")
        logger.info(f"  Alert Threshold:         {self.alert_threshold}")
        if self.enable_a2a:
            logger.info(f"  A2A Communication:       ENABLED")
            logger.info(f"    - Risk Agent A2A:      http://localhost:{self.risk_a2a_port}")
            logger.info(f"    - Nearest AP A2A:      http://localhost:{self.nearest_ap_a2a_port}")
        else:
            logger.info(f"  A2A Communication:       DISABLED (JSON file-based)")
        logger.info("="*70 + "\n")
        
        # Create tasks for all agents
        self.tasks = [
            asyncio.create_task(self.run_risk_agent()),
            asyncio.create_task(self.run_topology_agent()),
            asyncio.create_task(self.run_monitoring_agent())
        ]
        
        try:
            # Wait for all tasks
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            logger.info("Shutting down agents...")
    
    async def shutdown(self):
        """Shutdown all agents gracefully"""
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close all agents
        for name, agent in self.agents.items():
            logger.info(f"Closing {name} agent...")
            await agent.close()
        
        logger.info("✅ All agents shut down")


async def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    MULTI-AGENT NETWORK MONITORING WITH A2A                   ║
║                                                                              ║
║  Agent 1: Risk Score Calculation    - A2A Server on port 5001               ║
║  Agent 2: Nearest AP Recommendation - A2A Server on port 5002               ║
║  Agent 3: Network Monitoring        - A2A Client for on-demand queries      ║
║                                                                              ║
║  Data shared via JSON files + A2A protocol for real-time queries            ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Run all network monitoring agents with A2A")
    parser.add_argument("--risk-interval", type=int, default=10,
                        help="Risk calculation interval in seconds (default: 10)")
    parser.add_argument("--topology-interval", type=int, default=30,
                        help="Topology calculation interval in seconds (default: 30)")
    parser.add_argument("--monitor-interval", type=int, default=15,
                        help="Monitoring check interval in seconds (default: 15)")
    parser.add_argument("--alert-threshold", type=float, default=40.0,
                        help="Risk score threshold for alerts (default: 40)")
    parser.add_argument("--enable-a2a", action="store_true", default=True,
                        help="Enable A2A inter-agent communication (default: enabled)")
    parser.add_argument("--no-a2a", action="store_true", default=False,
                        help="Disable A2A communication (use JSON files only)")
    parser.add_argument("--risk-a2a-port", type=int, default=5001,
                        help="Risk Score Agent A2A port (default: 5001)")
    parser.add_argument("--nearest-a2a-port", type=int, default=5002,
                        help="Nearest AP Agent A2A port (default: 5002)")
    
    args = parser.parse_args()
    
    # Determine A2A state
    enable_a2a = not args.no_a2a
    
    # Create runner
    runner = MultiAgentRunner(
        risk_interval=args.risk_interval,
        topology_interval=args.topology_interval,
        monitor_interval=args.monitor_interval,
        alert_threshold=args.alert_threshold,
        enable_a2a=enable_a2a,
        risk_a2a_port=args.risk_a2a_port,
        nearest_ap_a2a_port=args.nearest_a2a_port
    )
    
    # Setup signal handler for graceful shutdown
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("\n⚠️ Received shutdown signal")
        asyncio.create_task(runner.shutdown())
    
    if sys.platform != "win32":
        loop.add_signal_handler(signal.SIGINT, signal_handler)
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
    
    # Initialize and run
    if not await runner.initialize_agents():
        logger.error("Failed to initialize agents")
        return
    
    try:
        await runner.run_all()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interrupted by user")
    finally:
        await runner.shutdown()
        logger.info("✅ Multi-agent system shut down")


if __name__ == "__main__":
    asyncio.run(main())
