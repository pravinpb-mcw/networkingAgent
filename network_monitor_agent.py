#!/usr/bin/env python3
"""
Network Change Detection Agent
Monitors network for changes and sends alerts via Teams/Slack webhooks
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from mcp_use import MCPAgent, MCPClient
from langchain.tools import tool
from mitigation_strategy_agent import MitigationStrategyAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Disable verbose MCP logging
logging.getLogger("mcp_use").setLevel(logging.ERROR)
logging.getLogger("mcp_use.agent").setLevel(logging.ERROR)
logging.getLogger("mcp_use.client").setLevel(logging.ERROR)

# Set environment variable to disable telemetry
os.environ["MCP_USE_ANONYMIZED_TELEMETRY"] = "false"

# Load environment variables
load_dotenv()

logger = logging.getLogger("network-monitor-agent")


class NetworkChangeDetector:
    """Detects network changes and sends alerts"""
    
    def __init__(self):
        self.client = None
        self.agent = None
        self.llm = None
        self.last_state = None
        self.mitigation_agent = None
        
        # Target device to monitor (matches simulation scripts)
        self.target_device = "Q2MN-Q3J9-YJHW"
        self.target_network = "L_3947405073390239794"
        
        self.baseline_metrics = {
            "latency_ms": 15.5,
            "packet_loss_pct": 0.1,
            "jitter_ms": 1.2,
            "goodput": 95.0
        }
        
        # Thresholds for alerts
        self.thresholds = {
            "latency_warning": 50.0,
            "latency_critical": 100.0,
            "loss_warning": 1.0,
            "loss_critical": 3.0,
            "jitter_warning": 10.0,
            "jitter_critical": 25.0,
            "goodput_warning": 80.0,
            "goodput_critical": 70.0
        }
    
    async def initialize(self):
        """Initialize the MCP client and agent"""
        try:
            # Set up Gemini API key
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                logger.error("GEMINI_API_KEY not found in .env file")
                return False
            
            os.environ["GEMINI_API_KEY"] = gemini_api_key
            
            # MCP server config file
            config_file = "mcp-inspector-config.json"
            
            logger.info("Initializing Network Change Detection Agent...")
            
            # Create MCP client
            logger.info("Connecting to MCP server...")
            self.client = MCPClient.from_config_file(config_file)
            
            # Create Anthropic LLM
            logger.info("Initializing Anthropic LLM (glm-4.5)...")
            self.llm = ChatAnthropic(
                model="glm-4.5",
                temperature=0,
                max_tokens=2048,
                timeout=None,
                max_retries=2,
                api_key=os.environ.get("ANTHROPIC_API_KEY", "55f27b9278af4b3a83a735e228ae4fb8.2oREoHAH8PdKM13f"),
                base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
            )
            
            # Initialize mitigation strategy agent
            logger.info("Initializing Mitigation Strategy Agent...")
            self.mitigation_agent = MitigationStrategyAgent()
            if not await self.mitigation_agent.initialize():
                logger.error("Failed to initialize mitigation agent")
                return False
            
            # Create tool wrapper for mitigation agent
            mitigation_tool = self._create_mitigation_tool()
            
            # Bind the mitigation tool to the LLM
            logger.info("Binding mitigation tool to LLM...")
            llm_with_tools = self.llm.bind_tools([mitigation_tool])
            
            # Create MCP agent with the enhanced LLM
            logger.info("Creating Network Change Detection Agent...")
            self.agent = MCPAgent(
                llm=llm_with_tools,
                client=self.client,
                max_steps=20,
                memory_enabled=True,
                verbose=False
            )
            
            logger.info("✅ Network Change Detection Agent initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return False
    
    def _create_mitigation_tool(self):
        """Create a tool wrapper for the mitigation strategy agent"""
        mitigation_agent = self.mitigation_agent
        target_device = self.target_device
        target_network = self.target_network
        
        @tool(
            "generate_mitigation_strategy",
            description="""Generate a comprehensive mitigation strategy for a detected network issue.
            
            Use this tool when:
            - Any network metric exceeds warning or critical thresholds
            - Uplink failures are detected
            - Performance degradation requires remediation
            
            This tool will provide:
            - Immediate actions to stabilize the situation
            - Short-term fixes and configuration adjustments
            - Investigation steps for root cause analysis
            - Long-term solutions and improvements
            - Preventive measures to avoid recurrence
            
            Args:
                issue_type: Type of issue detected (e.g., 'High Latency', 'Packet Loss', 'Uplink Failure')
                severity: Severity level - 'warning' or 'critical'
                current_latency_ms: Current latency in milliseconds
                current_packet_loss_pct: Current packet loss percentage
                current_jitter_ms: Current jitter in milliseconds
                uplink_status: Current uplink status (e.g., 'active', 'failed', 'connecting')
                additional_context: Any additional context about the issue
            
            Returns:
                Detailed mitigation strategy with actionable steps
            """
        )
        async def call_mitigation_agent(
            issue_type: str,
            severity: str,
            current_latency_ms: float,
            current_packet_loss_pct: float,
            current_jitter_ms: float,
            uplink_status: str = "unknown",
            additional_context: str = ""
        ) -> str:
            """Call the mitigation strategy agent"""
            metrics = {
                "latency_ms": current_latency_ms,
                "packet_loss_pct": current_packet_loss_pct,
                "jitter_ms": current_jitter_ms,
                "uplink_status": uplink_status
            }
            
            result = await mitigation_agent.generate_mitigation_strategy(
                issue_type=issue_type,
                severity=severity,
                metrics=metrics,
                device_serial=target_device,
                network_id=target_network,
                additional_context=additional_context
            )
            
            if result["success"]:
                return result["strategy"]
            else:
                return f"Error generating mitigation strategy: {result.get('error', 'Unknown error')}"
        
        return call_mitigation_agent
    
    async def close(self):
        """Close the MCP client and mitigation agent"""
        if self.mitigation_agent:
            await self.mitigation_agent.close()
        if self.client and hasattr(self.client, 'close_all_sessions'):
            await self.client.close_all_sessions()
    
    def get_monitoring_prompt(self) -> str:
        """Get the monitoring prompt for the agent"""
        return f"""You are a NETWORK CHANGE DETECTION AGENT with the following capabilities:

**PRIMARY MISSION:**
Detect and report network changes, performance degradation, and anomalies.

**TARGET MONITORING:**
- Device Serial: {self.target_device}
- Network ID: {self.target_network}
- ONLY monitor this specific device, ignore other devices in the organization

**AVAILABLE TOOLS:**
1. get_device_loss_and_latency_history - Check current network performance metrics for target device
2. get_organization_uplinks_statuses - Check uplink connectivity status (filter for target device)
3. get_network_clients - Check connected devices
4. get_network_events - Check for recent network events
5. send_network_alert - Send alerts to Teams/Slack webhooks

**DETECTION RULES:**

1. **LATENCY MONITORING:**
   - Normal: < 50ms
   - Warning: 50-100ms → Send warning alert
   - Critical: > 100ms → Send critical alert

2. **PACKET LOSS MONITORING:**
   - Normal: < 1%
   - Warning: 1-3% → Send warning alert
   - Critical: > 3% → Send critical alert

3. **JITTER MONITORING:**
   - Normal: < 10ms
   - Warning: 10-25ms → Send warning alert
   - Critical: > 25ms → Send critical alert

4. **UPLINK STATUS:**
   - Active: Normal
   - Connecting: Warning → Send warning alert
   - Failed: Critical → Send critical alert

5. **CLIENT CHANGES:**
   - Track number of online/offline clients
   - Alert if significant changes (>20% offline)

**EXECUTION STEPS:**
1. Call get_device_loss_and_latency_history to get latest metrics for device {self.target_device}
2. Analyze metrics against thresholds (look at the MOST RECENT entry in the history)
3. Call get_organization_uplinks_statuses and ONLY examine uplink status for device serial {self.target_device}
   - IGNORE all other devices in the organization
   - Focus ONLY on the target device's uplink status
4. If ANY metric exceeds thresholds OR target device uplinks have issues:
   - Call generate_mitigation_strategy tool with:
     * issue_type: Description of the issue (e.g., 'High Latency', 'Packet Loss')
     * severity: 'warning' or 'critical' based on thresholds
     * current_latency_ms: Latest latency value
     * current_packet_loss_pct: Latest packet loss value
     * current_jitter_ms: Latest jitter value
     * uplink_status: Current uplink status
     * additional_context: Any relevant context about the issue
   - Wait for the mitigation strategy to be generated
   - Then prepare detailed alert message including the mitigation strategy
   - Call send_network_alert with:
     * title: "Network Alert: [Issue Type]"
     * message: Include both issue description AND the mitigation strategy
     * status: "warning" or "critical"
     * metrics: Include current metrics
     * alerts: List of specific issues detected
5. Report your findings clearly for device {self.target_device} ONLY, including the mitigation strategy if generated

**ALERT MESSAGE FORMAT:**
```
Network Issue Detected at [timestamp]

ISSUE: [Brief description]

CURRENT METRICS:
- Latency: [value]ms (Threshold: [threshold]ms)
- Packet Loss: [value]% (Threshold: [threshold]%)
- Jitter: [value]ms (Threshold: [threshold]ms)
- Uplink Status: [status]

SEVERITY: [WARNING/CRITICAL]

DETAILS:
[Detailed description of the issue and potential impact]
```

**RESPONSE FORMAT:**
Always provide:
1. Current Status: [Normal/Warning/Critical] for device {self.target_device}
2. Metrics Summary: Current values vs thresholds (use MOST RECENT history entry)
3. Issues Detected: List any problems found on the target device
4. Alert Sent: Yes/No and to which platforms
5. Recommendation: What should be done next

**IMPORTANT:**
- Monitor ONLY device {self.target_device} - ignore all other devices
- Look at the MOST RECENT entry in device history (last item in the array)
- ALWAYS send alerts when thresholds are exceeded
- Be specific about what changed and why it matters
- Include timestamp and metric values in alerts
- Use "warning" status for non-critical issues
- Use "critical" status for severe issues
- Do NOT over-alert on minor fluctuations
- When checking uplinks, filter for serial {self.target_device} and ignore other devices"""
    
    async def check_network_state(self) -> Dict[str, Any]:
        """Check current network state and detect changes"""
        try:
            logger.info("🔍 Checking network state for changes...")
            
            monitoring_prompt = f"""{self.get_monitoring_prompt()}

**EXECUTE NOW:**
1. Check device loss and latency history - get the MOST RECENT (last) entry for device {self.target_device}
2. Check organization uplinks statuses - filter for device serial {self.target_device} ONLY
3. Compare the LATEST metrics against thresholds
4. If issues detected on target device, send alert via send_network_alert tool
5. Report findings for device {self.target_device}

**THRESHOLDS:**
- Latency: Warning @ {self.thresholds['latency_warning']}ms, Critical @ {self.thresholds['latency_critical']}ms
- Packet Loss: Warning @ {self.thresholds['loss_warning']}%, Critical @ {self.thresholds['loss_critical']}%
- Jitter: Warning @ {self.thresholds['jitter_warning']}ms, Critical @ {self.thresholds['jitter_critical']}ms

**START MONITORING DEVICE {self.target_device}:**"""
            
            # Run the agent
            response = await self.agent.run(monitoring_prompt)
            
            logger.info("✅ Network check complete")
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Error checking network state: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def continuous_monitoring(self, interval_seconds: int = 60):
        """Run continuous network monitoring"""
        logger.info(f"🚀 Starting continuous network monitoring (interval: {interval_seconds}s)")
        logger.info("="*60)
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"Monitoring Iteration #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}")
                
                # Check network state
                result = await self.check_network_state()
                
                if result["success"]:
                    logger.info(f"\n📊 MONITORING RESULT:")
                    logger.info(f"{'-'*60}")
                    print(result["response"])
                    logger.info(f"{'-'*60}")
                else:
                    logger.error(f"❌ Monitoring failed: {result.get('error', 'Unknown error')}")
                
                # Wait before next check
                logger.info(f"\n⏳ Waiting {interval_seconds} seconds until next check...")
                await asyncio.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Monitoring stopped by user")
        except Exception as e:
            logger.error(f"\n\n❌ Monitoring error: {e}")
    
    async def single_check(self):
        """Perform a single network check"""
        logger.info("🔍 Performing single network check...")
        logger.info("="*60)
        
        result = await self.check_network_state()
        
        if result["success"]:
            logger.info(f"\n📊 MONITORING RESULT:")
            logger.info(f"{'-'*60}")
            print(result["response"])
            logger.info(f"{'-'*60}")
        else:
            logger.error(f"❌ Check failed: {result.get('error', 'Unknown error')}")
        
        return result


async def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║        NETWORK CHANGE DETECTION AGENT                        ║
║                                                              ║
║  Monitors network for changes and sends alerts to Teams     ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Parse command line arguments
    mode = "single"
    interval = 15
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--continuous":
            mode = "continuous"
            if len(sys.argv) > 2:
                try:
                    interval = int(sys.argv[2])
                except ValueError:
                    logger.warning(f"Invalid interval '{sys.argv[2]}', using default 15s")
        elif sys.argv[1] in ["--help", "-h"]:
            print("\nUsage:")
            print("  python network_monitor_agent.py                    - Single check")
            print("  python network_monitor_agent.py --continuous [interval] - Continuous monitoring")
            print("  python network_monitor_agent.py --help             - Show this help")
            print("\nExamples:")
            print("  python network_monitor_agent.py --continuous 30    - Monitor every 30 seconds")
            print("  python network_monitor_agent.py --continuous 300   - Monitor every 5 minutes")
            return
    
    # Initialize the detector
    detector = NetworkChangeDetector()
    
    if not await detector.initialize():
        logger.error("Failed to initialize detector")
        return
    
    try:
        if mode == "continuous":
            logger.info(f"Starting continuous monitoring (interval: {interval}s)")
            await detector.continuous_monitoring(interval_seconds=interval)
        else:
            logger.info("Performing single network check")
            await detector.single_check()
    
    finally:
        await detector.close()
        logger.info("\n✅ Network Change Detection Agent shut down")


if __name__ == "__main__":
    asyncio.run(main())
