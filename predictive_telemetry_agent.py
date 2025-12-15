#!/usr/bin/env python3
"""
Predictive Telemetry Agent for Meraki Access Points
Monitors wireless metrics to predict AP failures before they occur
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from mcp_use import MCPAgent, MCPClient

# Load environment variables first
load_dotenv()
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-0e3ab579-b733-4eb2-806c-ec8992b533a0" 
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-3b7e7816-d943-4f19-94d7-036de2857a8a" 
os.environ["LANGFUSE_BASE_URL"] = "http://localhost:3000" 
# os.environ["LANGFUSE_BASE_URL"] = "https://us.cloud.langfuse.com" # 🇺🇸 US region
 
LANGFUSE_SECRET_KEY = "sk-lf-3b7e7816-d943-4f19-94d7-036de2857a8a"
LANGFUSE_PUBLIC_KEY = "pk-lf-0e3ab579-b733-4eb2-806c-ec8992b533a0"
LANGFUSE_BASE_URL = "http://localhost:3000"
# Import tracing module for Langfuse integration
from tracing import (
    verify_langfuse_connection,
    TracingContext,
    get_langfuse_handler,
    create_session_id,
    langfuse_client
)

# Verify Langfuse connection on startup
if verify_langfuse_connection():
    print("✅ Langfuse client is authenticated and ready!")
else:
    print("⚠️ Langfuse connection failed. Tracing will be limited.")

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

logger = logging.getLogger("predictive-telemetry-agent")



class PredictiveTelemetryAgent:
    """Predictive telemetry agent for AP failure detection"""
    
    def __init__(self):
        self.client = None
        self.agent = None
        self.llm = None
        
        # Session tracking for Langfuse
        self.session_id = create_session_id()
        self.user_id = "predictive-agent"
        
        # Target AP to monitor (from mock data)
        self.target_ap_serial = "Q2XX-ABCD-1234"
        self.target_ap_name = "AP-03"
        self.target_network = "L_3947405073390239794"
        
        # Risk scoring thresholds
        self.thresholds = {
            "latency_ms": {"stable": 30, "degrading": 60, "failure": 100},
            "jitter_ms": {"stable": 10, "degrading": 20, "failure": 30},
            "packet_loss_pct": {"stable": 1.0, "degrading": 3.0, "failure": 6.0},
            "channel_utilization_pct": {"stable": 70, "degrading": 85, "failure": 95},
            "retransmissions_per_min": {"stable": 20, "degrading": 35, "failure": 50},
            "signal_snr": {"stable": 25, "degrading": 20, "failure": 15},
            "auth_failures_per_hour": {"stable": 3, "degrading": 8, "failure": 15}
        }
        
        # Service impact mapping
        self.service_thresholds = {
            "Teams": {"latency": 150, "jitter": 30, "loss": 1.0},
            "Email": {"latency": 500, "jitter": 100, "loss": 5.0},
            "SMB": {"latency": 100, "jitter": 20, "loss": 0.5},
            "VOIP": {"latency": 150, "jitter": 30, "loss": 1.0}
        }
        
        logger.info(f"🔗 Session ID: {self.session_id}")
    
    async def initialize(self):
        """Initialize the MCP client and agent"""
        try:
            # Set up API keys
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                logger.error("GEMINI_API_KEY not found in .env file")
                return False
            
            os.environ["GEMINI_API_KEY"] = gemini_api_key
            
            # MCP server config file
            config_file = "mcp-inspector-config.json"
            
            logger.info("Initializing Predictive Telemetry Agent...")
            
            # Create MCP client
            logger.info("Connecting to MCP server...")
            self.client = MCPClient.from_config_file(config_file)
            
            # Create Anthropic LLM with Langfuse callback for tracing
            logger.info("Initializing Anthropic LLM with Langfuse tracing...")
            self.llm = ChatAnthropic(
                model="glm-4.5",
                temperature=0,
                max_tokens=4096,
                timeout=None,
                max_retries=2,
                api_key=os.environ.get("ANTHROPIC_API_KEY", "60b19768f0334766a3e3259590b14460.QTFX9bVQYgALL0Mj"),
                base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
                callbacks=[get_langfuse_handler()],  # Langfuse tracing
            )
            
            # Create MCP agent
            logger.info("Creating Predictive Telemetry Agent...")
            self.agent = MCPAgent(
                llm=self.llm,
                client=self.client,
                max_steps=30,
                memory_enabled=True,
                verbose=False
            )
            
            logger.info("✅ Predictive Telemetry Agent initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return False
    
    async def close(self):
        """Close the MCP client"""
        if self.client and hasattr(self.client, 'close_all_sessions'):
            await self.client.close_all_sessions()
    
    def get_predictive_monitoring_prompt(self) -> str:
        """Get the predictive monitoring prompt for the agent"""
        return f"""You are a PREDICTIVE WIRELESS TELEMETRY AGENT with advanced failure prediction capabilities.

**PRIMARY MISSION:**
Predict Access Point failures BEFORE they occur by analyzing telemetry trends and degradation patterns.

**TARGET MONITORING:**
- AP Name: {self.target_ap_name}
- AP Serial: {self.target_ap_serial}
- Network ID: {self.target_network}

**AVAILABLE TOOLS:**
1. get_ap_topology - Get nearby APs with distance, RSSI, channel overlap, floor proximity
2. get_wireless_health - Overall AP health score and metrics
3. get_wireless_usage_history - Time-series data: channel utilization, retransmissions, speed degradation
4. get_wireless_latency_history - Time-series latency, jitter, packet loss trends
5. get_wireless_failed_connections - Authentication and connectivity failures
6. get_device_clients - Clients currently connected to AP
7. get_network_traffic - L7 application traffic (Teams, Email, SMB, VOIP)
8. send_network_alert - Send predictive alerts to Teams/Slack

**CRITICAL: TREND ANALYSIS, NOT RAW VALUES**
- Analyze the DIRECTION and RATE OF CHANGE in metrics over time
- Look for GRADUAL DEGRADATION patterns across multiple metrics
- Compare CURRENT vs HISTORICAL values to detect anomalies
- Focus on TREND CORRELATION (e.g., rising jitter + rising retransmissions + falling SNR)

**RISK SCORING THRESHOLDS:**

**STABLE State (Risk Score: 0-20):**
- Latency: < {self.thresholds['latency_ms']['stable']}ms
- Jitter: < {self.thresholds['jitter_ms']['stable']}ms
- Packet Loss: < {self.thresholds['packet_loss_pct']['stable']}%
- Channel Utilization: < {self.thresholds['channel_utilization_pct']['stable']}%
- Retransmissions: < {self.thresholds['retransmissions_per_min']['stable']}/min
- SNR: > {self.thresholds['signal_snr']['stable']} dB
- Auth Failures: < {self.thresholds['auth_failures_per_hour']['stable']}/hour
- TREND: Flat or improving, no degradation pattern

**TEMPORARY DEGRADATION State (Risk Score: 21-40):**
- Metrics slightly elevated but TREND shows stabilization or recovery
- Latency: 25-40ms with flat or recovering trend
- Jitter: 5-15ms with intermittent spikes (not sustained)
- Packet Loss: 0.3-1.2% with recovery pattern
- Channel Utilization: 40-55% with stabilization
- Retransmissions: 8-18/min with no acceleration
- SNR: 28-33 dB with stable or recovering trend
- CRITICAL INDICATOR: Last 1-2 time buckets show stabilization or improvement
- EXPECTED OUTCOME: Will likely self-recover within 15-30 minutes
- ACTION: Monitor only, no intervention needed

**SUSTAINED DEGRADATION State (Risk Score: 41-70):**
- Metrics elevated AND TREND shows continuous worsening
- Latency: {self.thresholds['latency_ms']['stable']}-{self.thresholds['latency_ms']['degrading']}ms with upward trend
- Jitter: {self.thresholds['jitter_ms']['stable']}-{self.thresholds['jitter_ms']['degrading']}ms accelerating
- Packet Loss: {self.thresholds['packet_loss_pct']['stable']}-{self.thresholds['packet_loss_pct']['degrading']}% increasing
- Channel Utilization: {self.thresholds['channel_utilization_pct']['stable']}-{self.thresholds['channel_utilization_pct']['degrading']}% climbing
- Retransmissions: {self.thresholds['retransmissions_per_min']['stable']}-{self.thresholds['retransmissions_per_min']['degrading']}/min rising
- SNR: {self.thresholds['signal_snr']['failure']}-{self.thresholds['signal_snr']['degrading']} dB dropping
- Auth Failures: {self.thresholds['auth_failures_per_hour']['stable']}-{self.thresholds['auth_failures_per_hour']['degrading']}/hour
- CRITICAL INDICATOR: No recovery pattern, sustained worsening across 4+ time buckets
- EXPECTED OUTCOME: Will NOT self-recover, requires attention
- ACTION: Send warning alert, prepare for intervention

**LIKELY FAILURE State (Risk Score: 71-100):**
- Latency: > {self.thresholds['latency_ms']['degrading']}ms
- Jitter: > {self.thresholds['jitter_ms']['degrading']}ms
- Packet Loss: > {self.thresholds['packet_loss_pct']['degrading']}%
- Channel Utilization: > {self.thresholds['channel_utilization_pct']['degrading']}%
- Retransmissions: > {self.thresholds['retransmissions_per_min']['degrading']}/min
- SNR: < {self.thresholds['signal_snr']['failure']} dB
- Auth Failures: > {self.thresholds['auth_failures_per_hour']['degrading']}/hour
- CRITICAL INDICATOR: Rapid cascade, multiple critical thresholds breached
- EXPECTED OUTCOME: Imminent or active failure
- ACTION: Send CRITICAL alert, immediate intervention required

**EXECUTION STEPS:**

0. **Discover Nearby APs and Rank Candidates:**
   - Call get_ap_topology with network_id={self.target_network} and ap_serial={self.target_ap_serial}
   - For EACH nearby AP returned, call get_device_clients to check current client load
   - Rank all candidate APs by: Distance (30%), Signal RSSI (25%), Client Load (20%), Channel Overlap (15%), Same Floor (10%)
   - Select TOP 3 candidates for failover recommendation

1. **Collect Time-Series Telemetry:**
   - Call get_wireless_usage_history for AP {self.target_ap_serial}
   - Call get_wireless_latency_history for AP {self.target_ap_serial}
   - Call get_wireless_failed_connections for AP {self.target_ap_serial}
   - Call get_wireless_health for AP {self.target_ap_serial}

2. **Parse Telemetry for LLM Analysis:**
   - Extract TREND data, not just current values
   - Calculate rate of change: (latest - earliest) / time_period
   - Identify PATTERN: Is metric increasing, decreasing, or stable?
   - Look for CORRELATION: Are multiple metrics degrading together?

3. **Compute Risk Score (0-100):**
   - Analyze ALL metrics against thresholds
   - Weight heavily for TREND direction (e.g., latency increasing by 50% in 30 mins)
   - Factor in MULTIPLE simultaneous degradations
   - Consider HISTORICAL patterns vs current state
   
4. **LLM Classification:**
   Based on trends and risk score, classify as ONE of these FOUR states:
   - **Stable** (Risk 0-20): Healthy network, no action needed
   - **Temporary Degradation** (Risk 21-40): Minor transient issues, WILL self-recover, monitor only
   - **Sustained Degradation** (Risk 41-70): Worsening trend, will NOT self-recover, send warning alert
   - **Likely Failure** (Risk 71-100): Critical state, send critical alert, immediate intervention
   
   **KEY DIFFERENTIATOR between Temporary vs Sustained:**
   - Temporary: Last 1-2 time buckets show STABILIZATION or RECOVERY (values plateauing or improving)
   - Sustained: ALL time buckets show CONTINUOUS WORSENING (no recovery pattern visible)

5. **Client Impact Analysis:**
   - Call get_device_clients for AP {self.target_ap_serial}
   - Call get_network_traffic to identify L7 applications in use
   - Match client applications to service thresholds
   - Predict which services will be impacted

6. **Recommend Next Best AP:**
   - Get ALL nearby APs and query their status (client load, signal strength, health)
   - Rank candidates based on: distance, signal strength (RSSI), client load, channel overlap, same floor
   - Choose the BEST AP dynamically based on current metrics
   - Provide per-client recommendations with expected RSSI
   - Calculate switching timeline (e.g., "switch within 90 seconds")

7. **Send Predictive Alert:**
   - If Risk Score <= 20 (Stable): No alert needed
   - If Risk Score 21-40 (Temporary Degradation): Call send_network_alert with status="info"
   - If Risk Score 41-70 (Sustained Degradation): Call send_network_alert with status="warning"
   - If Risk Score > 70 (Likely Failure): Call send_network_alert with status="critical"
   
   Alert should include:
   - Title: "Predictive Alert: {self.target_ap_name} [Classification]"
   - Message: Include:
     * AP name and reason (e.g., "Jitter rising + uplink flapping")
     * Failure probability (Risk Score %)
     * Recovery likelihood assessment
     * Clients currently connected
     * Recommended AP to switch to (per client)
     * Expected service impact (Teams/Email/VOIP/SMB)
   - Status: "warning" for Sustained Degradation, "critical" for Likely Failure

**ALERT MESSAGE FORMAT:**
```
Predictive Failure Alert: {self.target_ap_name}

RISK CLASSIFICATION: [Stable/Temporary Degradation/Sustained Degradation/Likely Failure]
FAILURE PROBABILITY: [Risk Score]%
RECOVERY LIKELIHOOD: [High - will self-recover / Low - requires intervention / None - immediate action needed]
ESTIMATED TIME TO FAILURE: [N/A / 30-60 minutes / 5-10 minutes / Imminent]

TELEMETRY TRENDS (Time-Series Analysis):
- Latency: [value]ms → [value]ms (↑[trend]%) [RECOVERING/STABLE/WORSENING]
- Jitter: [value]ms → [value]ms (↑[trend]%) [RECOVERING/STABLE/WORSENING]
- Packet Loss: [value]% → [value]% (↑[trend]%) [RECOVERING/STABLE/WORSENING]
- Channel Utilization: [value]% → [value]% (↑[trend]%) [RECOVERING/STABLE/WORSENING]
- Retransmissions: [value]/min → [value]/min (↑[trend]%) [RECOVERING/STABLE/WORSENING]
- Signal SNR: [value]dB → [value]dB (↓[trend]%) [RECOVERING/STABLE/WORSENING]

TREND PATTERN: [Transient spike with recovery / Sustained worsening / Critical cascade]

REASON FOR ALERT:
[Detailed explanation of degradation pattern, e.g., "Jitter rising 65% + retransmissions doubling + SNR dropping 20% over 30 minutes"]

CONNECTED CLIENTS: [count]
- Anton-Laptop (10.0.0.101)
- Teams-Room (10.0.0.102)

SERVICE IMPACT PREDICTION:
- Teams Video Quality: [High/Medium/Low Risk]
- Email: [High/Medium/Low Risk]
- SMB File Transfers: [High/Medium/Low Risk]
- VOIP: [High/Medium/Low Risk]

RECOMMENDED ACTION:
[For Stable: No action needed]
[For Temporary Degradation: Continue monitoring, likely self-recovery within 15-30 minutes]
[For Sustained Degradation: Prepare failover to [AP Name], switch if no improvement in 5 minutes]
[For Likely Failure: IMMEDIATE switch to [AP Name] required]
- For each client: [AP Name] (Expected RSSI: [value] dBm, Load: [value]%)
- Ranking criteria: Distance, Signal Strength, Client Load, Channel Overlap, Same Floor

SWITCHING TIMELINE: [Not needed / Monitor for 15 min / Within 5 minutes / Immediate]
```

**RESPONSE FORMAT:**
Always provide:
1. **Risk Classification:** [Stable/Temporary Degradation/Sustained Degradation/Likely Failure]
2. **Risk Score:** [0-100]
3. **Recovery Likelihood:** [High/Low/None] with explanation
4. **Trend Analysis:** Summary of metric trends WITH recovery pattern indicator
5. **Client Impact:** List clients and affected services
6. **Recommended AP:** Next best AP with per-client details (if needed)
7. **Alert Sent:** Yes/No and to which platforms (only for Sustained/Likely Failure)
8. **Timeline:** When action should be taken (if any)

**IMPORTANT:**
- Focus on TRENDS, not absolute values
- Look for PATTERNS across multiple metrics
- DISTINGUISH between TEMPORARY (recovering) vs SUSTAINED (worsening) degradation
- Check the LAST 1-2 time buckets for recovery pattern to differentiate Temporary vs Sustained
- Be PROACTIVE - predict failures 5-10 minutes before they occur
- Provide ACTIONABLE recommendations with specific client switching instructions
- Include SERVICE IMPACT assessment in every alert
- Use time-series data to calculate RATE OF CHANGE
- Consider HISTORICAL baselines when assessing current state
- Send alerts for ALL degradation states (Temporary, Sustained, Likely Failure)
- For TEMPORARY DEGRADATION (Risk 21-40): Send "info" alert noting likely self-recovery
- For SUSTAINED DEGRADATION (Risk 41-70): Send "warning" alert
- For LIKELY FAILURE (Risk 71-100): Send "critical" alert"""
    
    async def run_predictive_analysis(self) -> Dict[str, Any]:
        """Run predictive analysis on target AP with Langfuse tracing"""
        
        # Create a trace for this analysis run
        with TracingContext(
            name=f"predictive-analysis-{self.target_ap_name}",
            session_id=self.session_id,
            user_id=self.user_id,
            tags=["predictive-telemetry", "monitoring", self.target_ap_name],
            metadata={
                "ap_serial": self.target_ap_serial,
                "ap_name": self.target_ap_name,
                "network_id": self.target_network
            }
        ) as ctx:
            try:
                logger.info(f"🔮 Running predictive analysis on {self.target_ap_name}...")
                logger.info(f"   Trace Session: {self.session_id[:8]}...")
                
                # Get the trace ID from the context for logging
                trace_id = ctx.trace_id
                logger.info(f"   Trace ID: {trace_id[:8] if trace_id else 'None'}...")
                
                # Create a NEW LLM instance with callback handler INSIDE the trace context
                # Pass parent trace_id so all LLM generations are nested under it
                llm_with_trace = ChatAnthropic(
                    model="glm-4.5",
                    temperature=0,
                    max_tokens=4096,
                    timeout=None,
                    max_retries=2,
                    api_key=os.environ.get("ANTHROPIC_API_KEY", "60b19768f0334766a3e3259590b14460.QTFX9bVQYgALL0Mj"),
                    base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
                    # Link all LLM calls to the parent trace via update_trace callback
                    callbacks=[get_langfuse_handler(parent_trace_id=trace_id)],
                )
                
                # Create a temporary agent with this trace-aware LLM
                agent_with_trace = MCPAgent(
                    llm=llm_with_trace,
                    client=self.client,
                    max_steps=30,
                    memory_enabled=True,
                    verbose=False
                )
                
                prompt = f"""{self.get_predictive_monitoring_prompt()}

**EXECUTE PREDICTIVE ANALYSIS NOW:**

0. First, discover and rank nearby APs using get_ap_topology(network_id="{self.target_network}", ap_serial="{self.target_ap_serial}"), then check client load on each candidate with get_device_clients
1. Collect all telemetry time-series data for AP {self.target_ap_serial}
2. Parse metrics and calculate TRENDS (rate of change, direction)
3. Check if LAST 1-2 time buckets show RECOVERY (stabilizing/improving) or CONTINUED WORSENING
4. Compute Risk Score (0-100) based on trend analysis:
   - Stable (0-20): All metrics healthy
   - Temporary Degradation (21-40): Elevated metrics BUT showing recovery pattern
   - Sustained Degradation (41-70): Elevated metrics with CONTINUED worsening
   - Likely Failure (71-100): Critical thresholds breached
5. Classify as Stable/Temporary Degradation/Sustained Degradation/Likely Failure
6. Identify clients and their application usage
7. Predict service impact (Teams/Email/SMB/VOIP)
8. Recommend next best AP (from ranked candidates) with per-client switching details
9. If Risk Score > 20, send predictive alert via send_network_alert:
   - Temporary Degradation (21-40): status="info", note likely recovery
   - Sustained Degradation (41-70): status="warning"
   - Likely Failure (71-100): status="critical"
10. Report comprehensive analysis with trend data and RECOVERY LIKELIHOOD assessment

**START ANALYSIS FOR AP {self.target_ap_serial}:**"""
                
                # Log the FULL prompt as input to the trace (required for LLM-as-a-judge)
                if ctx.span:
                    ctx.span.update(input={"prompt": prompt, "ap": self.target_ap_name})
                
                # Run the agent with the trace-aware LLM
                response = await agent_with_trace.run(prompt)
                
                # Log the FULL response as output (required for LLM-as-a-judge evaluation)
                if ctx.span:
                    ctx.span.update(
                        output={"response": str(response), "success": True},
                        metadata={"analysis_complete": True, "response_length": len(str(response))}
                    )
                    # Also update the trace level for evaluation features
                    ctx.span.update_trace(
                        input={"query": prompt},
                        output={"generation": str(response)}
                    )
                
                logger.info("✅ Predictive analysis complete")
                
                return {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "ap_serial": self.target_ap_serial,
                    "ap_name": self.target_ap_name,
                    "session_id": self.session_id,
                    "response": response
                }
                
            except Exception as e:
                logger.error(f"Error running predictive analysis: {e}")
                if ctx.span:
                    ctx.span.update(output={"error": str(e), "success": False})
                return {
                    "success": False,
                    "error": str(e),
                    "session_id": self.session_id
                }
    
    async def continuous_monitoring(self, interval_seconds: int = 120):
        """Run continuous predictive monitoring"""
        logger.info(f"🚀 Starting continuous predictive monitoring (interval: {interval_seconds}s)")
        logger.info("="*80)
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                logger.info(f"\n{'='*80}")
                logger.info(f"Monitoring Iteration #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"Target AP: {self.target_ap_name} ({self.target_ap_serial})")
                logger.info(f"{'='*80}")
                
                # Run predictive analysis
                result = await self.run_predictive_analysis()
                
                if result["success"]:
                    logger.info(f"\n📊 PREDICTIVE ANALYSIS RESULT:")
                    logger.info(f"{'-'*80}")
                    print(result["response"])
                    logger.info(f"{'-'*80}")
                else:
                    logger.error(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                
                # Wait before next check
                logger.info(f"\n⏳ Waiting {interval_seconds} seconds until next analysis...")
                await asyncio.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Monitoring stopped by user")
        except Exception as e:
            logger.error(f"\n\n❌ Monitoring error: {e}")
    
    async def single_analysis(self):
        """Perform a single predictive analysis"""
        logger.info("🔮 Performing single predictive analysis...")
        logger.info("="*80)
        
        result = await self.run_predictive_analysis()
        
        if result["success"]:
            logger.info(f"\n📊 PREDICTIVE ANALYSIS RESULT:")
            logger.info(f"{'-'*80}")
            print(result["response"])
            logger.info(f"{'-'*80}")
        else:
            logger.error(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
        
        return result


async def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║              PREDICTIVE TELEMETRY AGENT FOR MERAKI APs                       ║
║                                                                              ║
║  Predicts AP failures before they occur using AI-powered trend analysis     ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Parse command line arguments
    mode = "single"
    interval = 120  # 2 minutes default
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--continuous":
            mode = "continuous"
            if len(sys.argv) > 2:
                try:
                    interval = int(sys.argv[2])
                except ValueError:
                    logger.warning(f"Invalid interval '{sys.argv[2]}', using default 120s")
        elif sys.argv[1] in ["--help", "-h"]:
            print("\nUsage:")
            print("  python predictive_telemetry_agent.py                      - Single analysis")
            print("  python predictive_telemetry_agent.py --continuous [interval] - Continuous monitoring")
            print("  python predictive_telemetry_agent.py --help               - Show this help")
            print("\nExamples:")
            print("  python predictive_telemetry_agent.py --continuous 120     - Monitor every 2 minutes")
            print("  python predictive_telemetry_agent.py --continuous 300     - Monitor every 5 minutes")
            print("\nFeatures:")
            print("  • Predictive failure detection 5-10 minutes before AP fails")
            print("  • Trend analysis of latency, jitter, packet loss, channel utilization")
            print("  • Risk scoring: Stable (0-30), Degrading (31-70), Likely Failure (71-100)")
            print("  • Service impact prediction (Teams, Email, SMB, VOIP)")
            print("  • Intelligent AP failover recommendations with per-client details")
            print("  • Proactive alerts via Teams/Slack webhooks")
            return
    
    # Initialize the agent
    agent = PredictiveTelemetryAgent()
    
    if not await agent.initialize():
        logger.error("Failed to initialize agent")
        return
    
    try:
        if mode == "continuous":
            logger.info(f"Starting continuous predictive monitoring (interval: {interval}s)")
            await agent.continuous_monitoring(interval_seconds=interval)
        else:
            logger.info("Performing single predictive analysis")
            await agent.single_analysis()
    
    finally:
        await agent.close()
        logger.info("\n✅ Predictive Telemetry Agent shut down")


if __name__ == "__main__":
    asyncio.run(main())
