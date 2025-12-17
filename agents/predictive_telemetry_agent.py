#!/usr/bin/env python3
"""
Predictive Telemetry Agent for Meraki Access Points
Monitors wireless metrics to predict AP failures before they occur

Updated to use the latest LangChain patterns:
- langchain.agents.create_agent for agent creation
- langchain_mcp_adapters for MCP tool integration
- langchain.chat_models.init_chat_model for model initialization
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# New LangChain imports
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient

# Load environment variables first
load_dotenv()
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-05aedc22-20c5-43f0-b9bf-4aa500d749fe" 
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-864cdd54-cd46-42db-aacf-69233345b37e" 
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
logging.getLogger("langchain_mcp_adapters").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.WARNING)

logger = logging.getLogger("predictive-telemetry-agent")


@dataclass
class AgentContext:
    """Context schema for the predictive telemetry agent"""
    session_id: str
    user_id: str
    ap_serial: str
    ap_name: str
    network_id: str



class PredictiveTelemetryAgent:
    """Predictive telemetry agent for AP failure detection using LangChain create_agent"""
    
    def __init__(self):
        self.mcp_client: Optional[MultiServerMCPClient] = None
        self.agent = None
        self.tools = None
        
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
        """Initialize the MCP client and agent using langchain-mcp-adapters"""
        try:
            logger.info("Initializing Predictive Telemetry Agent with LangChain...")
            
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            server_path = os.path.join(script_dir, "server", "meraki_server.py")
            
            # Create MCP client using MultiServerMCPClient from langchain-mcp-adapters
            logger.info("Connecting to MCP server via langchain-mcp-adapters...")
            self.mcp_client = MultiServerMCPClient(
                {
                    "cisco-meraki-observability": {
                        "transport": "stdio",
                        "command": "python",
                        "args": [server_path],
                        "env": {
                            "TIMESPAN": "7200",
                            "BASE_URL": "https://api.meraki.com/api/v1",
                            "MOCK_BASE_URL": "http://127.0.0.1:5000",
                            "PRODUCT_TYPE": "appliance"
                        }
                    }
                }
            )
            
            # Get tools from MCP server
            logger.info("Loading tools from MCP server...")
            self.tools = await self.mcp_client.get_tools()
            logger.info(f"Loaded {len(self.tools)} tools from MCP server")
            
            # Create agent using LangChain's create_agent with init_chat_model
            logger.info("Creating agent with create_agent and init_chat_model...")
            
            # Initialize model using init_chat_model for flexibility
            # This supports model identifier strings and auto-inference
            model = init_chat_model(
                model="glm-4.5",
                model_provider="anthropic",  # Using OpenAI-compatible API
                temperature=0,
                max_tokens=4096,
                timeout=120,
                max_retries=2,
                api_key=os.environ.get("ANTHROPIC_API_KEY", "60b19768f0334766a3e3259590b14460.QTFX9bVQYgALL0Mj"),
                base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
            )
            
            # Create agent with system prompt and tools
            self.agent = create_agent(
                model=model,
                tools=self.tools,
                system_prompt=self.get_predictive_monitoring_prompt(),
                context_schema=AgentContext,
            )
            
            logger.info("✅ Predictive Telemetry Agent initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def close(self):
        """Close the MCP client connections"""
        # MultiServerMCPClient handles cleanup automatically
        # but we can explicitly close if needed
        if self.mcp_client:
            logger.info("Closing MCP client connections...")
            self.mcp_client = None
    
    def get_predictive_monitoring_prompt(self) -> str:
        """Get the predictive monitoring prompt for the agent"""
        return f"""You are a PREDICTIVE WIRELESS TELEMETRY AGENT with advanced failure prediction capabilities.

**PRIMARY MISSION:**
Predict Access Point failures BEFORE they occur by analyzing telemetry trends and degradation patterns.

**TARGET MONITORING:**
- AP Name: {self.target_ap_name}
- AP Serial: {self.target_ap_serial}
- Network ID: {self.target_network}

**⚠️ CRITICAL EXPLAINABILITY REQUIREMENT:**

BEFORE calling ANY tool, you MUST explain your reasoning using this EXACT format:

🔍 **REASONING FOR NEXT ACTION:**
Tool: [tool_name]
Why: [Explain in 1-2 sentences WHY you need to call this tool right now]
What I expect to find: [What specific information you're looking for]
How it helps: [How this data will contribute to the failure prediction]

Then call the tool.

AFTER receiving each tool result, provide analysis:

📊 **ANALYSIS OF RESULT:**
What I found: [Key findings from the tool output]
Significance: [What this means for AP health]
Next step: [What you'll do with this information]

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
   - If Risk Score 21-40 (Temporary Degradation): Call send_network_alert with status="normal"
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
- For TEMPORARY DEGRADATION (Risk 21-40): Send "normal" alert noting likely self-recovery
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
                
                # Build the analysis prompt
                prompt = f"""**EXECUTE PREDICTIVE ANALYSIS NOW:**

⚠️ REMEMBER: EXPLAIN YOUR REASONING BEFORE EVERY TOOL CALL using the format:

🔍 **REASONING FOR NEXT ACTION:**
Tool: [tool_name]
Why: [Why you need this tool now]
What I expect to find: [Specific information you're looking for]
How it helps: [Contribution to failure prediction]

Then call the tool, then analyze the result with:

📊 **ANALYSIS OF RESULT:**
What I found: [Key findings]
Significance: [What this means]
Next step: [What you'll do next]

**ANALYSIS STEPS:**

Step 0: EXPLAIN why you need get_ap_topology, then call it for network "{self.target_network}", ap "{self.target_ap_serial}"
        EXPLAIN findings, then check client load on each candidate AP

Step 1: EXPLAIN why you need each telemetry tool, call it, EXPLAIN what you discovered

Step 2: EXPLAIN your trend analysis methodology and findings

Step 3: EXPLAIN how you computed the Risk Score (0-100):
   - Stable (0-20): All metrics healthy
   - Temporary Degradation (21-40): Elevated BUT recovering
   - Sustained Degradation (41-70): Elevated AND worsening
   - Likely Failure (71-100): Critical thresholds breached

Step 4: EXPLAIN your classification decision

Step 5: EXPLAIN client impact analysis

Step 6: EXPLAIN AP recommendation logic

Step 7: If Risk Score > 20, EXPLAIN why you're sending alert, then call send_network_alert:
   - Temporary (21-40): status="normal", note recovery
   - Sustained (41-70): status="warning"
   - Likely Failure (71-100): status="critical"

Step 8: EXPLAIN final assessment with recovery likelihood

**START ANALYSIS FOR AP {self.target_ap_serial} - EXPLAIN EACH ACTION:**"""
                
                # Log the FULL prompt as input to the trace (required for LLM-as-a-judge)
                if ctx.span:
                    ctx.span.update(input={"prompt": prompt, "ap": self.target_ap_name})
                
                # Create context for the agent invocationxz
                agent_context = AgentContext(
                    session_id=self.session_id,
                    user_id=self.user_id,
                    ap_serial=self.target_ap_serial,
                    ap_name=self.target_ap_name,
                    network_id=self.target_network
                )
                
                # Invoke the agent using LangChain's create_agent pattern
                # The agent follows the ReAct loop automatically
                result = await self.agent.ainvoke(
                    {"messages": [{"role": "user", "content": prompt}]},
                    context=agent_context,
                    config={
                        "run_name": f"predictive-analysis-{self.target_ap_name}",
                        "tags": ["predictive-telemetry", "monitoring"],
                        "metadata": {
                            "ap_serial": self.target_ap_serial,
                            "session_id": self.session_id
                        },
                        "callbacks": [get_langfuse_handler(parent_trace_id=trace_id)],
                        "recursion_limit": 100,  # Increased from default 25 to allow explainability reasoning steps
                    }
                )
                
                # Extract the final response from the agent result
                # The result follows LangGraph's message state pattern
                messages = result.get("messages", [])
                final_response = ""
                if messages:
                    # Get the last AI message as the response
                    for msg in reversed(messages):
                        if hasattr(msg, 'content') and msg.content:
                            final_response = msg.content
                            break
                
                # Log the FULL response as output (required for LLM-as-a-judge evaluation)
                if ctx.span:
                    ctx.span.update(
                        output={"response": str(final_response), "success": True},
                        metadata={"analysis_complete": True, "response_length": len(str(final_response))}
                    )
                    # Also update the trace level for evaluation features
                    ctx.span.update_trace(
                        input={"query": prompt},
                        output={"generation": str(final_response)}
                    )
                
                logger.info("✅ Predictive analysis complete")
                
                return {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "ap_serial": self.target_ap_serial,
                    "ap_name": self.target_ap_name,
                    "session_id": self.session_id,
                    "response": final_response,
                    "full_result": result
                }
                
            except Exception as e:
                logger.error(f"Error running predictive analysis: {e}")
                import traceback
                traceback.print_exc()
                if ctx.span:
                    ctx.span.update(output={"error": str(e), "success": False})
                return {
                    "success": False,
                    "error": str(e),
                    "session_id": self.session_id
                }
    
    async def stream_predictive_analysis(self) -> Dict[str, Any]:
        """Run predictive analysis with streaming output"""
        
        logger.info(f"🔮 Running streaming predictive analysis on {self.target_ap_name}...")
        
        prompt = f"""**EXECUTE PREDICTIVE ANALYSIS NOW:**

0. First, discover and rank nearby APs using get_ap_topology(network_id="{self.target_network}", ap_serial="{self.target_ap_serial}")
1. Collect all telemetry time-series data for AP {self.target_ap_serial}
2. Parse metrics and calculate TRENDS
3. Compute Risk Score (0-100) and classify state
4. Send appropriate alert if needed

**START ANALYSIS FOR AP {self.target_ap_serial}:**"""

        agent_context = AgentContext(
            session_id=self.session_id,
            user_id=self.user_id,
            ap_serial=self.target_ap_serial,
            ap_name=self.target_ap_name,
            network_id=self.target_network
        )
        
        # Stream the agent's responses
        full_response = ""
        try:
            async for chunk in self.agent.astream(
                {"messages": [{"role": "user", "content": prompt}]},
                context=agent_context,
                stream_mode="values"
            ):
                # Each chunk contains the full state at that point
                messages = chunk.get("messages", [])
                if messages:
                    latest_message = messages[-1]
                    if hasattr(latest_message, 'content') and latest_message.content:
                        print(f"Agent: {latest_message.content}")
                        full_response = latest_message.content
                    elif hasattr(latest_message, 'tool_calls') and latest_message.tool_calls:
                        tool_names = [tc.get('name', 'unknown') for tc in latest_message.tool_calls]
                        print(f"Calling tools: {tool_names}")
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "response": full_response
            }
        except Exception as e:
            logger.error(f"Error in streaming analysis: {e}")
            return {
                "success": False,
                "error": str(e)
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
║                                                                              ║
║  Now using LangChain create_agent + langchain-mcp-adapters                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Parse command line arguments
    mode = "single"
    interval = 120  # 2 minutes default
    use_streaming = False
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--continuous":
            mode = "continuous"
            if len(sys.argv) > 2:
                try:
                    interval = int(sys.argv[2])
                except ValueError:
                    logger.warning(f"Invalid interval '{sys.argv[2]}', using default 120s")
        elif sys.argv[1] == "--stream":
            mode = "stream"
        elif sys.argv[1] in ["--help", "-h"]:
            print("\nUsage:")
            print("  python predictive_telemetry_agent.py                      - Single analysis")
            print("  python predictive_telemetry_agent.py --stream             - Single analysis with streaming")
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
            print("\nNew in this version:")
            print("  • Uses LangChain create_agent for production-ready agent implementation")
            print("  • Uses langchain-mcp-adapters for MCP tool integration")
            print("  • Supports streaming mode with --stream flag")
            print("  • Context-aware tools with ToolRuntime")
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
        elif mode == "stream":
            logger.info("Performing streaming predictive analysis")
            await agent.stream_predictive_analysis()
        else:
            logger.info("Performing single predictive analysis")
            await agent.single_analysis()
    
    finally:
        await agent.close()
        logger.info("\n✅ Predictive Telemetry Agent shut down")


if __name__ == "__main__":
    asyncio.run(main())






# #!/usr/bin/env python3
# """
# Predictive Telemetry Agent for Meraki Access Points
# Updated for LangChain 1.0

# Key Changes in LangChain 1.0:
# 1. context_schema must be a regular class (not TypedDict or dataclass with @dataclass)
# 2. AgentState must be TypedDict for state_schema
# 3. Proper separation between state (mutable conversation data) and context (immutable runtime data)
# 4. Explicit trace output logging for LLM-as-judge
# """

# import asyncio
# import json
# import logging
# import os
# import sys
# from typing import Dict, Any, Optional, List
# from typing_extensions import TypedDict
# from dotenv import load_dotenv

# # LangChain 1.0 imports
# from langchain.agents import create_agent, AgentState
# from langchain_mcp_adapters.client import MultiServerMCPClient
# from langchain_anthropic import ChatAnthropic  # Use proper provider

# # Load environment variables
# load_dotenv()

# # Set Langfuse credentials
# os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-05aedc22-20c5-43f0-b9bf-4aa500d749fe" 
# os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-864cdd54-cd46-42db-aacf-69233345b37e" 
# os.environ["LANGFUSE_BASE_URL"] = "http://localhost:3000"

# # Set Anthropic API credentials if not already in environment
# if "ANTHROPIC_API_KEY" not in os.environ:
#     os.environ["ANTHROPIC_API_KEY"] = "60b19768f0334766a3e3259590b14460.QTFX9bVQYgALL0Mj"
# if "ANTHROPIC_BASE_URL" not in os.environ:
#     os.environ["ANTHROPIC_BASE_URL"] = "https://api.z.ai/api/anthropic" 

# # Import tracing module
# from tracing import (
#     verify_langfuse_connection,
#     TracingContext,
#     get_langfuse_handler,
#     create_session_id,
#     langfuse_client
# )

# # Verify Langfuse connection
# if verify_langfuse_connection():
#     print("✅ Langfuse client is authenticated and ready!")
# else:
#     print("⚠️ Langfuse connection failed. Tracing will be limited.")

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logging.getLogger("langchain_mcp_adapters").setLevel(logging.WARNING)
# logging.getLogger("mcp").setLevel(logging.WARNING)
# logger = logging.getLogger("predictive-telemetry-agent")


# # ============================================================================
# # CRITICAL FIX FOR LANGCHAIN 1.0: Context Schema Must Be Plain Class
# # ============================================================================
# class AgentContext:
#     """
#     Context schema for runtime data (IMMUTABLE during execution).
#     In LangChain 1.0, context_schema MUST be a regular class, NOT TypedDict or dataclass.
#     """
#     def __init__(
#         self,
#         session_id: str,
#         user_id: str,
#         ap_serial: str,
#         ap_name: str,
#         network_id: str
#     ):
#         self.session_id = session_id
#         self.user_id = user_id
#         self.ap_serial = ap_serial
#         self.ap_name = ap_name
#         self.network_id = network_id


# # ============================================================================
# # OPTIONAL: Custom State Schema (if you need more than messages)
# # ============================================================================
# class CustomAgentState(AgentState):
#     """
#     Custom state schema extending AgentState.
#     In LangChain 1.0, state_schema MUST be TypedDict.
#     """
#     # AgentState already includes 'messages' field
#     # Add any additional fields your agent needs to track
#     analysis_count: int  # Track how many analyses have been run


# class PredictiveTelemetryAgent:
#     """Predictive telemetry agent for AP failure detection using LangChain 1.0"""
    
#     def __init__(self):
#         self.mcp_client: Optional[MultiServerMCPClient] = None
#         self.agent = None
#         self.tools = None
        
#         # Session tracking
#         self.session_id = create_session_id()
#         self.user_id = "predictive-agent"
        
#         # Target AP to monitor
#         self.target_ap_serial = "Q2XX-ABCD-1234"
#         self.target_ap_name = "AP-03"
#         self.target_network = "L_3947405073390239794"
        
#         # Risk scoring thresholds
#         self.thresholds = {
#             "latency_ms": {"stable": 30, "degrading": 60, "failure": 100},
#             "jitter_ms": {"stable": 10, "degrading": 20, "failure": 30},
#             "packet_loss_pct": {"stable": 1.0, "degrading": 3.0, "failure": 6.0},
#             "channel_utilization_pct": {"stable": 70, "degrading": 85, "failure": 95},
#             "retransmissions_per_min": {"stable": 20, "degrading": 35, "failure": 50},
#             "signal_snr": {"stable": 25, "degrading": 20, "failure": 15},
#             "auth_failures_per_hour": {"stable": 3, "degrading": 8, "failure": 15}
#         }
        
#         logger.info(f"🔗 Session ID: {self.session_id}")
    
#     async def initialize(self):
#         """Initialize the MCP client and agent using LangChain 1.0 patterns"""
#         try:
#             logger.info("Initializing Predictive Telemetry Agent with LangChain 1.0...")
            
#             # Get server path
#             script_dir = os.path.dirname(os.path.abspath(__file__))
#             server_path = os.path.join(script_dir, "server", "meraki_server.py")
            
#             # Create MCP client
#             logger.info("Connecting to MCP server...")
#             self.mcp_client = MultiServerMCPClient(
#                 {
#                     "cisco-meraki-observability": {
#                         "transport": "stdio",
#                         "command": "python",
#                         "args": [server_path],
#                         "env": {
#                             "TIMESPAN": "7200",
#                             "BASE_URL": "https://api.meraki.com/api/v1",
#                             "MOCK_BASE_URL": "http://127.0.0.1:5000",
#                             "PRODUCT_TYPE": "appliance"
#                         }
#                     }
#                 }
#             )
            
#             # Get tools
#             logger.info("Loading tools from MCP server...")
#             self.tools = await self.mcp_client.get_tools()
#             logger.info(f"Loaded {len(self.tools)} tools from MCP server")
            
#             # ========================================================================
#             # CRITICAL FIX: Use proper model initialization for LangChain 1.0
#             # ========================================================================
#             logger.info("Creating agent with LangChain 1.0 create_agent...")
            
#             # Get API key with fallback
#             api_key = os.environ.get("ANTHROPIC_API_KEY") or "60b19768f0334766a3e3259590b14460.QTFX9bVQYgALL0Mj"
#             base_url = os.environ.get("ANTHROPIC_BASE_URL") or "https://api.z.ai/api/anthropic"
            
#             logger.info(f"Using API base URL: {base_url}")
#             logger.info(f"API key configured: {'Yes' if api_key else 'No'}")
            
#             # Use ChatAnthropic directly (recommended approach)
#             model = ChatAnthropic(
#                 model="claude-sonnet-4-20250514",
#                 temperature=0,
#                 max_tokens=4096,
#                 timeout=120,
#                 max_retries=2,
#                 api_key=api_key,
#                 base_url=base_url,
#             )
            
#             # ========================================================================
#             # CRITICAL FIX: Use context_schema (NOT config_schema) in LangChain 1.0
#             # ========================================================================
#             self.agent = create_agent(
#                 model=model,
#                 tools=self.tools,
#                 system_prompt=self.get_predictive_monitoring_prompt(),
#                 context_schema=AgentContext,  # Plain class, not TypedDict
#                 # Optionally use custom state if you need more than messages:
#                 # state_schema=CustomAgentState,
#             )
            
#             logger.info("✅ Predictive Telemetry Agent initialized successfully!")
#             return True
            
#         except Exception as e:
#             logger.error(f"Failed to initialize: {e}")
#             import traceback
#             traceback.print_exc()
#             return False
    
#     async def close(self):
#         """Close the MCP client connections"""
#         if self.mcp_client:
#             logger.info("Closing MCP client connections...")
#             self.mcp_client = None
    
#     def get_predictive_monitoring_prompt(self) -> str:
#         """Get the predictive monitoring prompt for the agent"""
#         return f"""You are a PREDICTIVE WIRELESS TELEMETRY AGENT with advanced failure prediction capabilities.

# **PRIMARY MISSION:**
# Predict Access Point failures BEFORE they occur by analyzing telemetry trends and degradation patterns.

# **AVAILABLE TOOLS:**
# 1. get_ap_topology - Get nearby APs with distance, RSSI, channel overlap
# 2. get_wireless_health - Overall AP health score
# 3. get_wireless_usage_history - Time-series channel utilization, retransmissions
# 4. get_wireless_latency_history - Time-series latency, jitter, packet loss
# 5. get_wireless_failed_connections - Authentication failures
# 6. get_device_clients - Clients connected to AP
# 7. get_network_traffic - L7 application traffic
# 8. send_network_alert - Send alerts to Teams/Slack

# **EXECUTION STEPS:**
# 1. Collect telemetry time-series data
# 2. Analyze TRENDS (not just current values)
# 3. Compute Risk Score (0-100)
# 4. Classify: Stable/Temporary/Sustained/Likely Failure
# 5. Send appropriate alert if needed
# 6. Provide actionable recommendations

# **IMPORTANT:**
# - Focus on TREND ANALYSIS over time
# - Look for CORRELATED degradation patterns
# - Be PROACTIVE - predict failures 5-10 minutes ahead"""
    
#     async def run_predictive_analysis(self) -> Dict[str, Any]:
#         """
#         Run predictive analysis with PROPER OUTPUT LOGGING for LLM-as-judge.
        
#         CRITICAL FIX: The judge was failing because agent output wasn't being logged.
#         This version explicitly logs both input and output to the trace.
#         """
        
#         # Create trace context
#         with TracingContext(
#             name=f"predictive-analysis-{self.target_ap_name}",
#             session_id=self.session_id,
#             user_id=self.user_id,
#             tags=["predictive-telemetry", "monitoring", self.target_ap_name],
#             metadata={
#                 "ap_serial": self.target_ap_serial,
#                 "ap_name": self.target_ap_name,
#                 "network_id": self.target_network
#             }
#         ) as ctx:
#             try:
#                 logger.info(f"🔮 Running predictive analysis on {self.target_ap_name}...")
                
#                 # Build analysis prompt
#                 prompt = f"""**EXECUTE PREDICTIVE ANALYSIS:**

# 1. Collect telemetry for AP {self.target_ap_serial}
# 2. Analyze trends and compute Risk Score
# 3. Send alert if needed
# 4. Provide comprehensive report

# **START ANALYSIS NOW:**"""
                
#                 # ================================================================
#                 # CRITICAL FIX: Log input to trace (required for LLM-as-judge)
#                 # ================================================================
#                 if ctx.span:
#                     ctx.span.update(input={"prompt": prompt, "ap": self.target_ap_name})
                
#                 # Create context object (NOT dict, plain class instance)
#                 agent_context = AgentContext(
#                     session_id=self.session_id,
#                     user_id=self.user_id,
#                     ap_serial=self.target_ap_serial,
#                     ap_name=self.target_ap_name,
#                     network_id=self.target_network
#                 )
                
#                 # ================================================================
#                 # CRITICAL: Get Langfuse handler for agent invocation
#                 # ================================================================
#                 trace_id = ctx.trace_id
#                 langfuse_handler = get_langfuse_handler(parent_trace_id=trace_id)
                
#                 # ================================================================
#                 # Invoke agent with proper context and callbacks
#                 # ================================================================
#                 result = await self.agent.ainvoke(
#                     {"messages": [{"role": "user", "content": prompt}]},
#                     context=agent_context,  # Pass context object, not dict
#                     config={
#                         "run_name": f"predictive-analysis-{self.target_ap_name}",
#                         "tags": ["predictive-telemetry", "monitoring"],
#                         "metadata": {
#                             "ap_serial": self.target_ap_serial,
#                             "session_id": self.session_id
#                         },
#                         "callbacks": [langfuse_handler],
#                     }
#                 )
                
#                 # ================================================================
#                 # CRITICAL FIX: Extract and LOG final response
#                 # This is what was missing - the judge needs this output!
#                 # ================================================================
#                 messages = result.get("messages", [])
#                 final_response = ""
                
#                 if messages:
#                     # Get the last AI message
#                     for msg in reversed(messages):
#                         if hasattr(msg, 'content') and msg.content:
#                             final_response = msg.content
#                             break
                
#                 # ================================================================
#                 # CRITICAL FIX: Explicitly log output (THIS IS REQUIRED!)
#                 # Without this, judge sees empty "Model Output" and returns -1
#                 # ================================================================
#                 if ctx.span:
#                     ctx.span.update(
#                         output={
#                             "response": str(final_response),
#                             "success": True,
#                             "response_length": len(str(final_response))
#                         },
#                         metadata={
#                             "analysis_complete": True,
#                             "message_count": len(messages)
#                         }
#                     )
                    
#                     # ALSO update trace-level output for evaluation features
#                     ctx.span.update_trace(
#                         input={"query": prompt},
#                         output={"generation": str(final_response)}  # Judge looks here!
#                     )
                
#                 logger.info("✅ Predictive analysis complete")
#                 logger.info(f"📝 Response length: {len(str(final_response))} characters")
                
#                 return {
#                     "success": True,
#                     "timestamp": datetime.now().isoformat(),
#                     "ap_serial": self.target_ap_serial,
#                     "ap_name": self.target_ap_name,
#                     "session_id": self.session_id,
#                     "response": final_response,
#                     "full_result": result
#                 }
                
#             except Exception as e:
#                 logger.error(f"Error running predictive analysis: {e}")
#                 import traceback
#                 traceback.print_exc()
#                 if ctx.span:
#                     ctx.span.update(output={"error": str(e), "success": False})
#                 return {
#                     "success": False,
#                     "error": str(e),
#                     "session_id": self.session_id
#                 }
    
#     async def continuous_monitoring(self, interval_seconds: int = 120):
#         """Run continuous predictive monitoring"""
#         logger.info(f"🚀 Starting continuous monitoring (interval: {interval_seconds}s)")
        
#         iteration = 0
        
#         try:
#             while True:
#                 iteration += 1
#                 logger.info(f"\n{'='*80}")
#                 logger.info(f"Monitoring Iteration #{iteration}")
#                 logger.info(f"{'='*80}")
                
#                 result = await self.run_predictive_analysis()
                
#                 if result["success"]:
#                     logger.info(f"\n📊 ANALYSIS RESULT:")
#                     print(result["response"])
#                 else:
#                     logger.error(f"❌ Analysis failed: {result.get('error')}")
                
#                 logger.info(f"\n⏳ Waiting {interval_seconds}s...")
#                 await asyncio.sleep(interval_seconds)
                
#         except KeyboardInterrupt:
#             logger.info("\n\n⚠️ Monitoring stopped")
#         except Exception as e:
#             logger.error(f"\n\n❌ Monitoring error: {e}")
    
#     async def single_analysis(self):
#         """Perform a single predictive analysis"""
#         logger.info("🔮 Performing single predictive analysis...")
        
#         result = await self.run_predictive_analysis()
        
#         if result["success"]:
#             logger.info(f"\n📊 ANALYSIS RESULT:")
#             print(result["response"])
#         else:
#             logger.error(f"❌ Analysis failed: {result.get('error')}")
        
#         return result


# async def main():
#     """Main entry point"""
#     print("""
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║         PREDICTIVE TELEMETRY AGENT - LANGCHAIN 1.0 VERSION                   ║
# ║                                                                              ║
# ║  ✅ Fixed: LLM-as-Judge compatibility                                        ║
# ║  ✅ Fixed: Proper context_schema (plain class, not TypedDict)                ║
# ║  ✅ Fixed: Explicit output logging for evaluation                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#     """)
    
#     # Parse arguments
#     mode = "single"
#     interval = 120
    
#     if len(sys.argv) > 1:
#         if sys.argv[1] == "--continuous":
#             mode = "continuous"
#             if len(sys.argv) > 2:
#                 try:
#                     interval = int(sys.argv[2])
#                 except ValueError:
#                     logger.warning(f"Invalid interval, using default 120s")
#         elif sys.argv[1] in ["--help", "-h"]:
#             print("\nUsage:")
#             print("  python predictive_telemetry_agent.py                 - Single analysis")
#             print("  python predictive_telemetry_agent.py --continuous [interval]")
#             return
    
#     # Initialize agent
#     agent = PredictiveTelemetryAgent()
    
#     if not await agent.initialize():
#         logger.error("Failed to initialize agent")
#         return
    
#     try:
#         if mode == "continuous":
#             await agent.continuous_monitoring(interval_seconds=interval)
#         else:
#             await agent.single_analysis()
    
#     finally:
#         await agent.close()
#         logger.info("\n✅ Agent shut down")


# if __name__ == "__main__":
#     from datetime import datetime
#     asyncio.run(main())