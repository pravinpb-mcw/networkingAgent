#!/usr/bin/env python3
"""
Simple Monitor Agent Test
Tests if the monitor agent can initialize without dependencies.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "agents"))
sys.path.append(str(project_root / "core"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test-monitor")

async def test_monitor_agent():
    """Test monitor agent initialization"""
    try:
        logger.info("🧪 Testing Network Monitoring Agent initialization...")
        
        from agents.network_monitoring_agent import NetworkMonitoringAgent
        
        # Create agent with dependency auto-start disabled for testing
        agent = NetworkMonitoringAgent(alert_threshold=80)
        agent.auto_start_dependencies = False  # Disable auto-start for testing
        
        logger.info("Attempting to initialize agent...")
        success = await agent.initialize()
        
        if success:
            logger.info("✅ Agent initialized successfully!")
            
            # Test a simple monitoring check
            logger.info("Testing monitoring check...")
            
            try:
                # Run one monitoring check
                result = await agent.run_monitoring_check()
                logger.info(f"✅ Monitoring check completed: {result}")
            except Exception as check_error:
                logger.error(f"❌ Monitoring check failed: {check_error}")
        else:
            logger.error("❌ Agent initialization failed")
        
        await agent.close()
        logger.info("🧪 Test complete")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_monitor_agent())