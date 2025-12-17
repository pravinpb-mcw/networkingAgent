#!/usr/bin/env python3
"""
Network Monitoring Agent (Agent 3)
Monitors risk data from Agent 1 and uses Agent 2's nearest AP data for recommendations.

Features:
- Continuously monitors risk_scores.json from Agent 1
- When at-risk APs are detected, looks up nearest_aps.json from Agent 2
- A2A Client to query Agent 1 and Agent 2 on demand
- Generates comprehensive failure predictions and recommendations
- Sends alerts via Teams/Slack webhooks
- Provides actionable failover guidance with per-client recommendations
"""

import asyncio
import json
import logging
import os
import sys
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# LangChain imports
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient

# A2A imports
try:
    from python_a2a import A2AClient, Message, TextContent, MessageRole, Conversation
    A2A_AVAILABLE = True
except ImportError:
    A2A_AVAILABLE = False
    logging.warning("python-a2a not installed. A2A client features will be disabled. Install with: pip install python-a2a")

# Load environment variables
load_dotenv()

# Langfuse configuration
os.environ["LANGFUSE_PUBLIC_KEY"] = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-05aedc22-20c5-43f0-b9bf-4aa500d749fe")
os.environ["LANGFUSE_SECRET_KEY"] = os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-864cdd54-cd46-42db-aacf-69233345b37e")
os.environ["LANGFUSE_BASE_URL"] = os.getenv("LANGFUSE_BASE_URL", "http://localhost:3000")

# Import tracing module
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))
from tracing import (
    verify_langfuse_connection,
    TracingContext,
    get_langfuse_handler,
    create_session_id,
    langfuse_client
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("langchain_mcp_adapters").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.WARNING)
logger = logging.getLogger("network-monitoring-agent")


# ============================================================================
# A2A Client for Inter-Agent Communication
# ============================================================================

class A2AAgentClient:
    """Client for communicating with Agent 1 (Risk Score) and Agent 2 (Nearest AP) via A2A"""
    
    def __init__(self, risk_agent_url: str = "http://localhost:5001", 
                 nearest_ap_agent_url: str = "http://localhost:5002"):
        self.risk_agent_url = risk_agent_url
        self.nearest_ap_url = nearest_ap_agent_url
        self.risk_client = None
        self.nearest_ap_client = None
        
        if A2A_AVAILABLE:
            try:
                self.risk_client = A2AClient(risk_agent_url)
                logger.info(f"✅ Connected to Risk Score Agent at {risk_agent_url}")
            except Exception as e:
                logger.warning(f"⚠️ Could not connect to Risk Score Agent: {e}")
            
            try:
                self.nearest_ap_client = A2AClient(nearest_ap_agent_url)
                logger.info(f"✅ Connected to Nearest AP Agent at {nearest_ap_agent_url}")
            except Exception as e:
                logger.warning(f"⚠️ Could not connect to Nearest AP Agent: {e}")
    
    def _create_message(self, query: str) -> Message:
        """Create an A2A message from a query"""
        return Message(
            content=TextContent(text=query),
            role=MessageRole.USER
        )
    
    def query_risk_agent(self, query: str) -> Optional[Dict[str, Any]]:
        """Query the Risk Score Agent (Agent 1) via A2A"""
        if not self.risk_client:
            logger.warning("Risk Score Agent not available")
            return None
        
        try:
            logger.info(f"📡 Querying Risk Score Agent: {query[:50]}...")
            conversation = Conversation()
            conversation.add_message(self._create_message(query))
            
            response = self.risk_client.send(conversation)
            
            if response and response.messages:
                last_message = response.messages[-1]
                if hasattr(last_message.content, 'text'):
                    try:
                        return json.loads(last_message.content.text)
                    except json.JSONDecodeError:
                        return {"raw_response": last_message.content.text}
            
            return None
        except Exception as e:
            logger.error(f"Error querying Risk Score Agent: {e}")
            return None
    
    def query_nearest_ap_agent(self, query: str) -> Optional[Dict[str, Any]]:
        """Query the Nearest AP Agent (Agent 2) via A2A"""
        if not self.nearest_ap_client:
            logger.warning("⚠️ Nearest AP Agent A2A client not available")
            logger.warning("   Make sure Agent 2 is running with: python nearest_ap_agent.py --continuous 30 --a2a-port 5002")
            return None
        
        try:
            logger.info(f"📡 A2A QUERY → Agent 2 (Nearest AP)")
            logger.info(f"   Query: {query}")
            logger.info(f"   URL: {self.nearest_ap_url}")
            
            conversation = Conversation()
            conversation.add_message(self._create_message(query))
            
            response = self.nearest_ap_client.send(conversation)
            
            if response and response.messages:
                last_message = response.messages[-1]
                if hasattr(last_message.content, 'text'):
                    logger.info(f"✅ A2A RESPONSE ← Agent 2")
                    logger.info(f"   Response length: {len(last_message.content.text)} chars")
                    try:
                        data = json.loads(last_message.content.text)
                        logger.info(f"   Parsed as JSON - Success: {data.get('success', 'N/A')}")
                        return data
                    except json.JSONDecodeError:
                        logger.warning(f"   Response not JSON, returning as raw text")
                        return {"raw_response": last_message.content.text}
            
            logger.warning(f"⚠️ No response from Agent 2")
            return None
        except Exception as e:
            logger.error(f"❌ Error querying Nearest AP Agent: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_all_risk_scores(self) -> Optional[Dict[str, Any]]:
        """Get all current risk scores from Agent 1"""
        return self.query_risk_agent("Get all risk scores")
    
    def get_at_risk_aps(self, threshold: float = 40.0) -> Optional[Dict[str, Any]]:
        """Get at-risk APs above threshold from Agent 1"""
        return self.query_risk_agent(f"Get at-risk APs with risk score >= {threshold}")
    
    def get_ap_risk_score(self, ap_serial: str) -> Optional[Dict[str, Any]]:
        """Get risk score for a specific AP from Agent 1"""
        return self.query_risk_agent(f"Get risk score for AP {ap_serial}")
    
    def get_failover_recommendation(self, ap_serial: str) -> Optional[Dict[str, Any]]:
        """Get failover recommendation for an AP from Agent 2"""
        return self.query_nearest_ap_agent(f"Get failover recommendation for AP {ap_serial}")
    
    def get_nearest_aps(self, ap_serial: str) -> Optional[Dict[str, Any]]:
        """Get nearest APs for a specific AP from Agent 2"""
        return self.query_nearest_ap_agent(f"Get nearest APs for AP {ap_serial}")
    
    def get_limited_failover_aps(self, min_candidates: int = 2) -> Optional[Dict[str, Any]]:
        """Get APs with limited failover options from Agent 2"""
        return self.query_nearest_ap_agent(f"Get APs with fewer than {min_candidates} failover options")


@dataclass
class MonitoringAgentContext:
    """Context schema for the network monitoring agent"""
    session_id: str
    user_id: str
    network_id: str
    check_interval: int
    alert_threshold: float


class NetworkMonitoringAgent:
    """
    Agent 3: Network Monitoring Agent
    
    Monitors Agent 1's risk data and uses Agent 2's topology data
    to provide comprehensive failure predictions and recommendations.
    Supports A2A communication for real-time queries to sub-agents.
    """
    
    def __init__(self, check_interval: int = 15, alert_threshold: float = 40.0,
                 enable_a2a: bool = True, risk_agent_port: int = 5001, 
                 nearest_ap_agent_port: int = 5002):
        self.mcp_client: Optional[MultiServerMCPClient] = None
        self.agent = None
        self.tools = None
        
        # Configuration
        self.check_interval = check_interval
        self.alert_threshold = alert_threshold  # Risk score threshold for alerts
        self.session_id = create_session_id()
        self.user_id = "network-monitoring-agent"
        self.network_id = "L_3947405073390239794"
        
        # A2A Client for inter-agent communication
        self.enable_a2a = enable_a2a
        self.a2a_client: Optional[A2AAgentClient] = None
        if enable_a2a and A2A_AVAILABLE:
            logger.info(f"🔗 Initializing A2A client...")
            logger.info(f"   Agent 1 (Risk Score): http://localhost:{risk_agent_port}")
            logger.info(f"   Agent 2 (Nearest AP): http://localhost:{nearest_ap_agent_port}")
            self.a2a_client = A2AAgentClient(
                risk_agent_url=f"http://localhost:{risk_agent_port}",
                nearest_ap_agent_url=f"http://localhost:{nearest_ap_agent_port}"
            )
        elif not A2A_AVAILABLE:
            logger.warning("⚠️ python-a2a not installed - A2A features disabled")
            logger.warning("   Install with: pip install python-a2a")
        
        # Service impact thresholds
        self.service_thresholds = {
            "Teams": {"latency": 150, "jitter": 30, "loss": 1.0},
            "Email": {"latency": 500, "jitter": 100, "loss": 5.0},
            "SMB": {"latency": 100, "jitter": 20, "loss": 0.5},
            "VOIP": {"latency": 150, "jitter": 30, "loss": 1.0}
        }
        
        # Track previously alerted APs to avoid spam
        self.alerted_aps: Dict[str, datetime] = {}
        self.alert_cooldown = 300  # 5 minutes cooldown between alerts for same AP
        
        # Data paths for reading from other agents (file-based communication)
        self.agent_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agent_data")
        os.makedirs(self.agent_data_dir, exist_ok=True)
        self.risk_scores_file = os.path.join(self.agent_data_dir, "risk_scores.json")
        self.nearest_aps_file = os.path.join(self.agent_data_dir, "nearest_aps.json")
        
        # Dependency agent management
        self.risk_agent_port = risk_agent_port
        self.nearest_ap_agent_port = nearest_ap_agent_port
        self.dependency_processes = {}  # Track spawned processes
        self.auto_start_dependencies = True
        
        logger.info(f"🔗 Network Monitoring Agent Session: {self.session_id}")
        logger.info(f"   Alert threshold: Risk Score >= {self.alert_threshold}")
        if self.a2a_client:
            logger.info(f"   A2A enabled: Risk Agent port {risk_agent_port}, Nearest AP port {nearest_ap_agent_port}")
        logger.info(f"   Reading data from: {self.agent_data_dir}")
    
    def _check_port_in_use(self, port: int) -> bool:
        """Check if a port is in use (indicating agent is running)"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result == 0
        except:
            return False
    
    def _start_dependency_agent(self, agent_name: str, script_name: str, port: int) -> bool:
        """Start a dependency agent if not running"""
        if self._check_port_in_use(port):
            logger.info(f"✅ {agent_name} already running on port {port}")
            return True
        
        try:
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            agent_path = os.path.join(script_dir, "agents", script_name)
            
            if not os.path.exists(agent_path):
                logger.error(f"❌ Agent script not found: {agent_path}")
                return False
            
            # Find the correct Python executable (use virtual env if available)
            python_exe = sys.executable
            
            # Check if there's a .wenv in parent directory
            parent_dir = os.path.dirname(script_dir)
            venv_python = os.path.join(parent_dir, ".wenv", "Scripts", "python.exe")
            if os.path.exists(venv_python):
                python_exe = venv_python
                logger.debug(f"   Using virtual environment: {venv_python}")
            
            logger.info(f"🚀 Starting {agent_name} on port {port}...")
            logger.debug(f"   Script path: {agent_path}")
            logger.debug(f"   Working directory: {script_dir}")
            logger.debug(f"   Python executable: {python_exe}")
            
            # Start the process with better error handling
            # Use the same Python executable that's running this script (respects virtual env)
            process = subprocess.Popen(
                [python_exe, agent_path, "--continuous"],  # Add continuous mode for dependency agents
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=script_dir,
                text=True,
                env=os.environ.copy()  # Pass current environment (includes virtual env)
            )
            
            self.dependency_processes[agent_name] = process
            
            # Wait and check startup
            for attempt in range(1, 6):  # 5 attempts, 1 second each
                time.sleep(1)
                if process.poll() is not None:
                    # Process died, get error info
                    stdout, stderr = process.communicate()
                    logger.error(f"❌ {agent_name} process died during startup")
                    logger.error(f"   Exit code: {process.returncode}")
                    if stderr:
                        logger.error(f"   Error: {stderr[:1000]}")  # Show more error details
                    if stdout:
                        logger.error(f"   Output: {stdout[:500]}")
                    return False
                
                if self._check_port_in_use(port):
                    logger.info(f"✅ {agent_name} started successfully (attempt {attempt})")
                    return True
                
                logger.debug(f"   Waiting for {agent_name} startup (attempt {attempt}/5)...")
            
            logger.warning(f"⚠️ {agent_name} may not have started properly")
            logger.info(f"   Process status: {'running' if process.poll() is None else 'stopped'}")
            return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start {agent_name}: {e}")
            return False
    
    async def _ensure_dependencies_running(self) -> bool:
        """Ensure dependency agents are running, start them if needed"""
        if not self.auto_start_dependencies:
            return True
        
        logger.info("🔍 Checking dependency agents...")
        
        # Check and start Risk Score Agent (Agent 1)
        risk_ok = self._start_dependency_agent(
            "Risk Score Agent (Agent 1)", 
            "risk_score_agent.py", 
            self.risk_agent_port
        )
        
        # Check and start Nearest AP Agent (Agent 2)
        nearest_ok = self._start_dependency_agent(
            "Nearest AP Agent (Agent 2)", 
            "nearest_ap_agent.py", 
            self.nearest_ap_agent_port
        )
        
        if risk_ok and nearest_ok:
            logger.info("✅ All dependency agents are running")
            return True
        else:
            logger.warning("⚠️ Some dependency agents failed to start")
            logger.info("   Monitor agent will continue but may have limited functionality")
            return False
    
    async def initialize(self) -> bool:
        """Initialize the MCP client and agent"""
        try:
            logger.info("Initializing Network Monitoring Agent...")
            
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            server_path = os.path.join(script_dir, "server", "meraki_server.py")
            
            # Create MCP client
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
            
            # Get tools
            logger.info("Loading MCP tools...")
            self.tools = await self.mcp_client.get_tools()
            logger.info(f"Loaded {len(self.tools)} tools")
            
            # Initialize model
            model = init_chat_model(
                model="claude-sonnet-4-20250514",
                model_provider="anthropic",
                temperature=0,
                max_tokens=8192,
                timeout=180,
                max_retries=2,
                api_key=os.environ.get("ANTHROPIC_API_KEY", "60b19768f0334766a3e3259590b14460.QTFX9bVQYgALL0Mj"),
                base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
            )
            
            # Create agent with system prompt
            self.agent = create_agent(
                model=model,
                tools=self.tools,
                system_prompt=self.get_system_prompt(),
                context_schema=MonitoringAgentContext,
            )
            
            logger.info("✅ Network Monitoring Agent initialized!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _read_risk_scores(self) -> Dict[str, Any]:
        """Read risk scores from Agent 1's JSON file"""
        try:
            if os.path.exists(self.risk_scores_file):
                with open(self.risk_scores_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"⚠️ Risk scores file not found: {self.risk_scores_file}")
                logger.info("   Make sure Agent 1 (Risk Score) is running")
                return {}
        except Exception as e:
            logger.error(f"Error reading risk scores: {e}")
            return {}
    
    def _read_nearest_aps(self) -> Dict[str, Any]:
        """Read nearest AP recommendations from Agent 2's JSON file"""
        try:
            if os.path.exists(self.nearest_aps_file):
                with open(self.nearest_aps_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"⚠️ Nearest APs file not found: {self.nearest_aps_file}")
                logger.info("   Make sure Agent 2 (Nearest AP) is running")
                return {}
        except Exception as e:
            logger.error(f"Error reading nearest APs: {e}")
            return {}
    
    async def close(self):
        """Close the MCP client"""
        if self.mcp_client:
            logger.info("Closing MCP client...")
            self.mcp_client = None
    
    async def query_sub_agents_via_a2a(self) -> Dict[str, Any]:
        """Query Agent 1 and Agent 2 via A2A protocol"""
        if not self.a2a_client:
            return {"success": False, "error": "A2A client not available"}
        
        logger.info("📡 Querying sub-agents via A2A...")
        
        results = {
            "success": True,
            "risk_data": None,
            "at_risk_aps": None,
            "failover_data": {}
        }
        
        # Get at-risk APs from Agent 1
        at_risk_result = self.a2a_client.get_at_risk_aps(self.alert_threshold)
        if at_risk_result and at_risk_result.get("success"):
            results["at_risk_aps"] = at_risk_result
            logger.info(f"   Found {at_risk_result.get('count', 0)} at-risk APs")
            
            # For each at-risk AP, get failover recommendation from Agent 2
            for ap in at_risk_result.get("at_risk_aps", []):
                ap_serial = ap.get("ap_serial")
                if ap_serial:
                    failover = self.a2a_client.get_failover_recommendation(ap_serial)
                    if failover:
                        results["failover_data"][ap_serial] = failover
        else:
            # Get all risk scores as fallback
            results["risk_data"] = self.a2a_client.get_all_risk_scores()
        
        return results
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for network monitoring"""
        return f"""You are AGENT 3: Network Monitoring Agent - Keep reports SHORT and ACTIONABLE.

## REQUIRED OUTPUT FORMAT:

**IF ALL APs ARE HEALTHY (all risk scores < {self.alert_threshold}):**
```
✅ **ALL SYSTEMS HEALTHY**
All APs operating normally. Risk scores below threshold.
```

**IF ANY AP AT RISK (risk score >= {self.alert_threshold}):**
```
## 📡 ALL AP TOPOLOGY
- [AP1 Serial]: Risk [X]/100 - [Status] - [X] clients
- [AP2 Serial]: Risk [X]/100 - [Status] - [X] clients
- [AP3 Serial]: Risk [X]/100 - [Status] - [X] clients
Overall Network Health: [X]/100

## ⚠️ WHICH IS AFFECTED
- **At-Risk APs:** [AP Serial(s)] with risk scores [X]/100
- **Clients Impacted:** [X] clients - [Client names/IPs]
- **Services:** Teams ([RISK LEVEL]), Email ([RISK LEVEL]), File Transfers ([RISK LEVEL])

## 🔍 REASON
[Brief 2-3 sentence explanation of WHY the AP is degraded]
Key metrics: Latency [X]ms, Jitter [X]ms, Loss [X]%, SNR [X]dB
Trend: [Improving/Stable/Degrading]

## ✅ RECOMMENDED ACTIONS
- **Immediate:** [Action if urgent, or "Monitor for [X] minutes"]
- **Failover Target:** [Best AP Serial] (Score [X]/100, [X]m away, Signal [X]dBm)
- **Timeline:** [When to act - e.g., "Within 60 min" or "No immediate action needed"]
```

## RULES:
- Keep explanations under 3 sentences
- NO scenario names in output
- Focus on WHAT to do, not why in detail
- If all healthy, just say "All systems healthy" and STOP

Network ID: {self.network_id}
Alert Threshold: {self.alert_threshold}"""
    
    async def run_monitoring_check(self) -> Dict[str, Any]:
        """Run a monitoring check for at-risk APs"""
        
        with TracingContext(
            name="network-monitoring-check",
            session_id=self.session_id,
            user_id=self.user_id,
            tags=["network-monitoring-agent", "health-check"],
            metadata={
                "network_id": self.network_id,
                "alert_threshold": self.alert_threshold
            }
        ) as ctx:
            try:
                logger.info("🔍 Running network monitoring check...")
                
                # Read data from Agent 1 and Agent 2 JSON files
                risk_scores_data = self._read_risk_scores()
                nearest_aps_data = self._read_nearest_aps()
                
                # Build context from JSON files
                context_info = f"""
**DATA FROM AGENT 1 (Risk Scores):**
{json.dumps(risk_scores_data, indent=2) if risk_scores_data else "No data available"}

**DATA FROM AGENT 2 (Nearest APs):**
{json.dumps(nearest_aps_data, indent=2) if nearest_aps_data else "No data available"}
"""
                
                prompt = f"""# NETWORK OPERATIONS CENTER - MONITORING ANALYSIS

**Network ID:** {self.network_id}
**Alert Threshold:** Risk Score >= {self.alert_threshold}
**Analysis Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Report Type:** Comprehensive Risk & Failover Analysis

---
## AVAILABLE DATA FROM OTHER AGENTS:

{context_info}

---
## YOUR TASK:

Analyze the data provided above from Agent 1 (Risk Scores) and Agent 2 (Nearest APs).

1. **Identify At-Risk Access Points**: Look for APs with risk scores >= {self.alert_threshold}

2. **Summarize Key Issues**: 
   - Which APs are at risk and why?
   - What are the performance trends?
   - What is the impact on users/applications?

3. **Provide Recommendations**:
   - Should clients be moved to failover APs?
   - Which failover APs are recommended (from Agent 2 data)?
   - What actions should network operators take?

4. **Format your response clearly** with:
   - Risk classification (CRITICAL/WARNING/STABLE)
   - Summary of at-risk APs
   - Recommended failover candidates
   - Action items for operators

**BEGIN ANALYSIS:**

### 🔄 RECOVERY LIKELIHOOD: [predictions.recoveryLikelihood]
**Reason:** [predictions.recoveryReason]

---
### 📈 TREND ANALYSIS:

**CRITICAL DEGRADATION PATTERNS:** (from predictions.trendAnalysis)
- **Channel Utilization:** [start]% → [end]% (↑[change]% - **[trend]**)
- **Airtime Utilization:** [start]% → [end]% (↑[change]% - **[trend]**)
- **Retransmissions:** [start]/min → [end]/min (↑[change]% - **[trend]**)
- **Signal SNR:** [start]dB → [end]dB (↓[change]% - **[trend]**)
- **Speed Degradation:** Uplink ↓[uplinkSpeed.change]%, Downlink ↓[downlinkSpeed.change]%
- **Client Load:** [start] → [end] clients (↑[change]% - **[trend]**)

**CURRENT PERFORMANCE vs CRITICAL THRESHOLDS:** (from predictions.currentThresholds)
- **Latency:** [value]ms (Critical: >[threshold]ms [status])
- **Jitter:** [value]ms (Critical: >[threshold]ms [status])
- **Packet Loss:** [value]% (Critical: >[threshold]% [status])

**TREND PATTERN:** **[pattern]**

---
### 👥 CLIENT IMPACT:

**CONNECTED CLIENTS:** [from get_device_clients]
- **[ClientName]** ([IP]) - [Device type] - [Usage level]

**SERVICE IMPACT PREDICTION:** (from predictions.applications)
- **Teams Video:** **[impactLevel] RISK** - [notes]
- **SSH Sessions:** **[impactLevel] RISK** - [notes]
- **File Transfers:** **[impactLevel] RISK** - [notes]
- **VOIP:** **[impactLevel] RISK** - [notes]

---
### 🎯 RANKED FAILOVER CANDIDATES: (from predictions.failoverCandidates)

**🥇 TOP RECOMMENDATION: [apName] ([apSerial])**
- **Score:** [score]/100 - [reason]
- **Distance:** [distance]m, **Channel Overlap:** [channelOverlap], **Same Floor:** [sameFloor]
- **Per-Client Migration:** [clientExpectations]

**🥈 SECONDARY: [apName] ([apSerial])**
- **Score:** [score]/100 - [reason]

**🥉 TERTIARY: [apName] ([apSerial])**
- **Score:** [score]/100 - [reason]

---
### 📱 ALERT SENT:
✅ **Teams:** [Alert status]

---
### ⏰ IMMEDIATE ACTION REQUIRED:
**SWITCHING TIMELINE:** **Within [estimatedTimeToFailure]** - [interventionPriority]

**EXECUTION PLAN:** (from predictions.executionPlan)
1. [step 1]
2. [step 2]
3. [step 3]
4. [step 4]

**ESTIMATED TIME TO FAILURE:** [predictions.estimatedTimeToFailure]
**INTERVENTION PRIORITY:** **[predictions.interventionPriority]**
```

---
⚠️ **CRITICAL REQUIREMENTS:**
1. MUST call `get_service_impact_predictions` - this provides ALL professional data
2. MUST call `get_failover_recommendation` - this provides the ranked AP list from Agent 2
3. MUST show ALL 3 failover candidates (🥇🥈🥉) with their scores
4. MUST use trendAnalysis data for trend deltas
5. MUST include executionPlan steps exactly as returned

**BEGIN ANALYSIS NOW** → Start with `get_at_risk_aps`, then `get_service_impact_predictions`:"""

                if ctx.span:
                    ctx.span.update(input={"prompt": prompt, "threshold": self.alert_threshold})
                
                agent_context = MonitoringAgentContext(
                    session_id=self.session_id,
                    user_id=self.user_id,
                    network_id=self.network_id,
                    check_interval=self.check_interval,
                    alert_threshold=self.alert_threshold
                )
                
                trace_id = ctx.trace_id
                
                # Safety check for agent
                if self.agent is None:
                    logger.error("\u274c Agent not initialized - cannot run monitoring check")
                    logger.info("\ud83d\udca1 Try restarting the agent or check MCP server status")
                    return {
                        "success": False,
                        "error": "Agent not initialized",
                        "timestamp": datetime.now().isoformat(),
                        "session_id": self.session_id
                    }
                
                result = await self.agent.ainvoke(
                    {"messages": [{"role": "user", "content": prompt}]},
                    context=agent_context,
                    config={
                        "run_name": "network-monitoring-check",
                        "tags": ["monitoring", "health-check"],
                        "metadata": {"network_id": self.network_id},
                        "callbacks": [get_langfuse_handler(parent_trace_id=trace_id)],
                        "recursion_limit": 50,
                    }
                )
                
                # Extract response
                messages = result.get("messages", [])
                final_response = ""
                if messages:
                    for msg in reversed(messages):
                        if hasattr(msg, 'content') and msg.content:
                            final_response = msg.content
                            break
                
                if ctx.span:
                    ctx.span.update(
                        output={"response": str(final_response), "success": True}
                    )
                
                logger.info("✅ Monitoring check complete")
                
                return {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "session_id": self.session_id,
                    "response": final_response
                }
                
            except Exception as e:
                logger.error(f"Error in monitoring check: {e}")
                import traceback
                traceback.print_exc()
                if ctx.span:
                    ctx.span.update(output={"error": str(e), "success": False})
                return {
                    "success": False,
                    "error": str(e),
                    "session_id": self.session_id
                }
    
    async def continuous_monitoring(self):
        """Run continuous network monitoring"""
        logger.info(f"🚀 Starting continuous network monitoring (interval: {self.check_interval}s)")
        logger.info(f"   Alert threshold: {self.alert_threshold}")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                logger.info(f"\n{'='*70}")
                logger.info(f"Monitoring Check #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*70}")
                
                result = await self.run_monitoring_check()
                
                if result["success"]:
                    logger.info(f"🔍 Check complete")
                    # Print response (show full professional report)
                    response = result["response"]
                    if len(response) > 5000:
                        print(response[:5000] + "\n... [truncated]")
                    else:
                        print(response)
                else:
                    logger.error(f"❌ Check failed: {result.get('error')}")
                
                logger.info(f"⏳ Next check in {self.check_interval}s...")
                await asyncio.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️ Network monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
    
    async def single_check(self):
        """Perform a single monitoring check"""
        logger.info("🔍 Performing single monitoring check...")
        
        result = await self.run_monitoring_check()
        
        if result["success"]:
            print("\n" + "="*70)
            print("NETWORK MONITORING REPORT")
            print("="*70)
            print(result["response"])
            print("="*70)
        else:
            logger.error(f"❌ Check failed: {result.get('error')}")
        
        return result


async def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    NETWORK MONITORING AGENT (Agent 3)                        ║
║                                                                              ║
║  Monitors Agent 1 risk data and uses Agent 2 topology for recommendations   ║
║  A2A Client for on-demand inter-agent communication                         ║
║  Sends alerts and provides comprehensive failover guidance                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Parse arguments
    mode = "single"
    interval = 15
    threshold = 40.0
    enable_a2a = True
    risk_agent_port = 5001
    nearest_ap_port = 5002
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--continuous":
            mode = "continuous"
            if i + 1 < len(args) and not args[i+1].startswith("--"):
                try:
                    interval = int(args[i+1])
                    i += 1
                except ValueError:
                    pass
        elif args[i] == "--threshold":
            if i + 1 < len(args):
                try:
                    threshold = float(args[i+1])
                    i += 1
                except ValueError:
                    pass
        elif args[i] == "--no-a2a":
            enable_a2a = False
        elif args[i] == "--risk-port":
            if i + 1 < len(args):
                try:
                    risk_agent_port = int(args[i+1])
                    i += 1
                except ValueError:
                    pass
        elif args[i] == "--nearest-port":
            if i + 1 < len(args):
                try:
                    nearest_ap_port = int(args[i+1])
                    i += 1
                except ValueError:
                    pass
        elif args[i] in ["--help", "-h"]:
            print("\nUsage:")
            print("  python network_monitoring_agent.py                        - Single check")
            print("  python network_monitoring_agent.py --continuous [sec]     - Continuous mode")
            print("  python network_monitoring_agent.py --threshold [score]    - Set alert threshold")
            print("  python network_monitoring_agent.py --no-a2a               - Disable A2A communication")
            print("  python network_monitoring_agent.py --risk-port [port]     - Risk Agent A2A port (default 5001)")
            print("  python network_monitoring_agent.py --nearest-port [port]  - Nearest AP Agent A2A port (default 5002)")
            print("  python network_monitoring_agent.py --help                 - Show this help")
            print("\nExamples:")
            print("  python network_monitoring_agent.py --continuous 15        - Check every 15s")
            print("  python network_monitoring_agent.py --threshold 30         - Alert on risk >= 30")
            print("  python network_monitoring_agent.py --continuous 10 --threshold 50")
            print("  python network_monitoring_agent.py --risk-port 5001 --nearest-port 5002")
            print("\nA2A Communication:")
            print("  This agent can communicate with Agent 1 and Agent 2 via A2A protocol.")
            print("  Make sure the sub-agents are running with A2A enabled:")
            print("    - Agent 1 (Risk Score): python risk_score_agent.py --continuous --a2a-port 5001")
            print("    - Agent 2 (Nearest AP): python nearest_ap_agent.py --continuous --a2a-port 5002")
            return
        i += 1
    
    # Verify Langfuse
    if verify_langfuse_connection():
        print("✅ Langfuse connected")
    else:
        print("⚠️ Langfuse not available")
    
    if enable_a2a and A2A_AVAILABLE:
        print(f"✅ A2A enabled: Risk Agent port {risk_agent_port}, Nearest AP port {nearest_ap_port}")
    elif not A2A_AVAILABLE:
        print("⚠️ A2A not available (python-a2a not installed)")
    else:
        print("ℹ️ A2A disabled")
    
    # Initialize agent
    agent = NetworkMonitoringAgent(
        check_interval=interval, 
        alert_threshold=threshold,
        enable_a2a=enable_a2a,
        risk_agent_port=risk_agent_port,
        nearest_ap_agent_port=nearest_ap_port
    )
    
    if not await agent.initialize():
        logger.error("Failed to initialize agent")
        return
    
    try:
        if mode == "continuous":
            await agent.continuous_monitoring()
        else:
            await agent.single_check()
    finally:
        await agent.close()
        logger.info("✅ Network Monitoring Agent shut down")


if __name__ == "__main__":
    asyncio.run(main())
