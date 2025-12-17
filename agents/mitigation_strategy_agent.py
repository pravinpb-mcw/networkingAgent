#!/usr/bin/env python3
"""
Mitigation Strategy Agent
Generates detailed mitigation guidelines and remediation steps for network issues
"""

import asyncio
import logging
import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from mcp_use import MCPAgent, MCPClient

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

logger = logging.getLogger("mitigation-strategy-agent")


class MitigationStrategyAgent:
    """Specialized agent for generating network issue mitigation strategies"""
    
    def __init__(self):
        self.client = None
        self.agent = None
        self.llm = None
        
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
            
            logger.info("Initializing Mitigation Strategy Agent...")
            
            # Create MCP client
            logger.info("Connecting to MCP server...")
            self.client = MCPClient.from_config_file(config_file)
            
            # Create Anthropic LLM
            logger.info("Initializing Anthropic LLM (glm-4.5)...")
            self.llm = ChatAnthropic(
                model="glm-4.5",
                temperature=0.3,  # Slightly higher for creative solutions
                max_tokens=4096,  # More tokens for detailed strategies
                timeout=None,
                max_retries=2,
                api_key=os.environ.get("ANTHROPIC_API_KEY", "55f27b9278af4b3a83a735e228ae4fb8.2oREoHAH8PdKM13f"),
                base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
            )
            
            # Create MCP agent
            logger.info("Creating Mitigation Strategy Agent...")
            self.agent = MCPAgent(
                llm=self.llm,
                client=self.client,
                max_steps=20,
                memory_enabled=True,
                verbose=False
            )
            
            logger.info("✅ Mitigation Strategy Agent initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return False
    
    async def close(self):
        """Close the MCP client"""
        if self.client and hasattr(self.client, 'close_all_sessions'):
            await self.client.close_all_sessions()
    
    def get_mitigation_prompt(self) -> str:
        """Get the base mitigation strategy prompt"""
        return """You are a NETWORK MITIGATION STRATEGY SPECIALIST with deep expertise in:

**CORE COMPETENCIES:**
- Network troubleshooting and diagnostics
- Meraki infrastructure optimization
- Performance tuning and capacity planning
- Failover and redundancy strategies
- Root cause analysis and remediation

**YOUR MISSION:**
Generate comprehensive, actionable mitigation strategies for network issues based on:
1. Current network metrics and performance data
2. Uplink status and connectivity issues
3. Client impact and service degradation
4. Historical patterns and trends

**AVAILABLE TOOLS:**
- get_device_loss_and_latency_history: Analyze historical performance
- get_organization_uplinks_statuses: Check uplink configurations
- get_network_settings: Review network configuration
- get_connectivity_monitoring: Check monitoring settings
- update_connectivity_monitoring: Adjust monitoring thresholds
- update_uplink: Modify uplink configurations
- update_appliance_settings: Change appliance settings
- get_access_control_lists: Review ACL configurations
- get_security_intrusion: Check security settings

**MITIGATION STRATEGY STRUCTURE:**

1. **IMMEDIATE ACTIONS** (0-5 minutes)
   - Critical steps to stabilize the situation
   - Emergency failover procedures
   - Quick wins to reduce impact

2. **SHORT-TERM FIXES** (5-30 minutes)
   - Configuration adjustments
   - Traffic rerouting
   - Threshold tuning
   - Service restoration steps

3. **INVESTIGATION STEPS** (parallel with fixes)
   - Root cause analysis procedures
   - Data collection commands
   - Diagnostic checks
   - Historical trend review

4. **LONG-TERM SOLUTIONS** (1-24 hours)
   - Infrastructure improvements
   - Capacity planning
   - Redundancy enhancements
   - Monitoring optimization

5. **PREVENTIVE MEASURES** (ongoing)
   - Configuration best practices
   - Proactive monitoring setup
   - Alerting improvements
   - Documentation updates

**OUTPUT FORMAT:**
Your response MUST be structured, detailed, and actionable. Include:
- Specific CLI commands or API calls where applicable
- Expected outcomes for each step
- Rollback procedures for risky changes
- Estimated time to execute each phase
- Risk assessment for each action
- Prerequisites and dependencies

**DECISION CRITERIA:**
- Prioritize service availability over optimization
- Balance quick fixes with sustainable solutions
- Consider business impact and SLA requirements
- Account for maintenance windows and change control
- Evaluate risk vs. benefit for each action

**IMPORTANT:**
- Always provide rationale for recommendations
- Include specific metric thresholds and values
- Mention which tools/APIs to use for each action
- Consider dependencies between mitigation steps
- Highlight any actions requiring human approval"""
    
    async def generate_mitigation_strategy(
        self,
        issue_type: str,
        severity: str,
        metrics: Dict[str, Any],
        device_serial: str,
        network_id: str,
        additional_context: str = ""
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive mitigation strategy for a detected network issue
        
        Args:
            issue_type: Type of issue (latency, packet_loss, uplink_failure, etc.)
            severity: Severity level (warning, critical)
            metrics: Current network metrics
            device_serial: Affected device serial number
            network_id: Network ID
            additional_context: Any additional context about the issue
            
        Returns:
            Dict containing the mitigation strategy
        """
        try:
            logger.info(f"🔧 Generating mitigation strategy for {issue_type} ({severity})")
            
            prompt = f"""{self.get_mitigation_prompt()}

**INCIDENT DETAILS:**

Issue Type: {issue_type}
Severity: {severity.upper()}
Device Serial: {device_serial}
Network ID: {network_id}

**CURRENT METRICS:**
{self._format_metrics(metrics)}

**ADDITIONAL CONTEXT:**
{additional_context if additional_context else "No additional context provided"}

**TASK:**
Generate a comprehensive mitigation strategy following the structure outlined above.

**EXECUTION STEPS:**
1. First, gather current configuration data:
   - Call get_device_loss_and_latency_history for {device_serial} to see trends
   - Call get_organization_uplinks_statuses for device {device_serial} to check uplink config
   - Call get_network_settings for {network_id} to review current settings
   - Call get_connectivity_monitoring for {network_id} to check monitoring config

2. Based on the issue type ({issue_type}) and severity ({severity}), analyze:
   - What is the root cause?
   - What is the immediate impact?
   - What configuration changes could help?
   - What are the risks of each mitigation option?

3. Generate the detailed mitigation strategy with all 5 phases:
   - IMMEDIATE ACTIONS
   - SHORT-TERM FIXES
   - INVESTIGATION STEPS
   - LONG-TERM SOLUTIONS
   - PREVENTIVE MEASURES

4. For each recommended action, specify:
   - Exact steps to execute
   - Which MCP tool to use (if applicable)
   - Expected outcome
   - Time to complete
   - Risk level (low/medium/high)
   - Rollback procedure

**START ANALYSIS:**"""
            
            # Run the agent
            response = await self.agent.run(prompt)
            
            logger.info("✅ Mitigation strategy generated")
            
            return {
                "success": True,
                "issue_type": issue_type,
                "severity": severity,
                "device_serial": device_serial,
                "network_id": network_id,
                "strategy": response,
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"Error generating mitigation strategy: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format metrics for display"""
        if not metrics:
            return "No metrics provided"
        
        lines = []
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                lines.append(f"- {key}: {value}")
            else:
                lines.append(f"- {key}: {value}")
        
        return "\n".join(lines)


async def test_mitigation_agent():
    """Test function to run the mitigation agent standalone"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║        MITIGATION STRATEGY AGENT - TEST MODE                 ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    agent = MitigationStrategyAgent()
    
    if not await agent.initialize():
        logger.error("Failed to initialize agent")
        return
    
    try:
        # Example test case - high latency issue
        result = await agent.generate_mitigation_strategy(
            issue_type="High Latency",
            severity="warning",
            metrics={
                "latency_ms": 75.5,
                "packet_loss_pct": 0.5,
                "jitter_ms": 15.3,
                "goodput": 88.0
            },
            device_serial="Q2MN-Q3J9-YJHW",
            network_id="L_3947405073390239794",
            additional_context="Latency has been gradually increasing over the past 30 minutes. No uplink failures detected."
        )
        
        if result["success"]:
            print("\n" + "="*80)
            print("MITIGATION STRATEGY:")
            print("="*80)
            print(result["strategy"])
            print("="*80)
        else:
            print(f"\n❌ Failed to generate strategy: {result.get('error')}")
    
    finally:
        await agent.close()
        logger.info("\n✅ Test complete")


if __name__ == "__main__":
    asyncio.run(test_mitigation_agent())
