#!/usr/bin/env python3
"""
Risk Score Calculation Agent (Agent 1)
Calculates risk scores for all Access Points at regular intervals.

Features:
- Parallel MCP tool calling for efficient data collection
- Risk score calculation using weighted formula:
  RISK_SCORE = 0.25*latency + 0.20*jitter + 0.20*retransmission + 
               0.15*snr_degradation + 0.10*client_load + 0.10*auth_failure_rate
- Stores results in JSON for other agents to consume
- Runs continuously with configurable interval (default 10s)
- A2A Server for inter-agent communication
"""

import asyncio
import json
import logging
import os
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "core"))

# LangChain imports
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient

# A2A imports
try:
    from python_a2a import A2AServer, agent, skill, run_server
    A2A_AVAILABLE = True
except ImportError:
    A2A_AVAILABLE = False
    print("⚠️ python-a2a not installed. A2A features disabled. Install with: pip install python-a2a")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("langchain_mcp_adapters").setLevel(logging.ERROR)
logging.getLogger("mcp").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logger = logging.getLogger("risk-score-agent")


@dataclass
class RiskAgentContext:
    """Context schema for the risk score calculation agent"""
    session_id: str
    user_id: str
    network_id: str
    calculation_interval: int


class RiskScoreCalculationAgent:
    """
    Agent 1: Risk Score Calculation Agent
    
    Calculates risk scores for all APs using parallel tool calls.
    Stores results in JSON for the Network Monitoring Agent to consume.
    """
    
    def __init__(self, calculation_interval: int = 10):
        self.mcp_client: Optional[MultiServerMCPClient] = None
        self.agent = None
        self.tools = None
        
        # Configuration
        self.calculation_interval = calculation_interval
        self.session_id = f"risk-agent-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.user_id = "risk-score-agent"
        self.network_id = "L_3947405073390239794"
        
        # Risk score weights
        self.weights = {
            "latency": 0.25,
            "jitter": 0.20,
            "retransmission": 0.20,
            "snr_degradation": 0.15,
            "client_load": 0.10,
            "auth_failure_rate": 0.10
        }
        
        # Thresholds for metric scoring (0-100 scale)
        self.thresholds = {
            "latency_ms": {"good": 30, "warning": 60, "critical": 100},
            "jitter_ms": {"good": 10, "warning": 20, "critical": 30},
            "packet_loss_pct": {"good": 1.0, "warning": 3.0, "critical": 6.0},
            "retransmissions_per_min": {"good": 20, "warning": 35, "critical": 50},
            "snr_db": {"good": 25, "warning": 20, "critical": 15},  # Lower is worse
            "client_count": {"good": 20, "warning": 40, "critical": 60},
            "auth_failures_per_hour": {"good": 3, "warning": 8, "critical": 15}
        }
        
    
    async def initialize(self) -> bool:
        """Initialize the MCP client and agent"""
        try:
            
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            server_path = os.path.join(script_dir, "server", "meraki_server.py")
            
            # Try to initialize MCP client
            mcp_success = False
            try:
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
                self.tools = await self.mcp_client.get_tools()
                logger.info(f"✅ Loaded {len(self.tools)} MCP tools successfully")
                mcp_success = True
                
            except Exception as mcp_error:
                logger.error(f"❌ MCP initialization failed: {mcp_error}")
                logger.warning("⚠️ Continuing without MCP tools - limited functionality")
                self.tools = []
                self.mcp_client = None
            
            # Initialize model
            model = init_chat_model(
                model="claude-sonnet-4-20250514",
                model_provider="anthropic",
                temperature=0,
                max_tokens=512,
                timeout=60,
                max_retries=1,
                api_key=os.environ.get("ANTHROPIC_API_KEY", "60b19768f0334766a3e3259590b14460.QTFX9bVQYgALL0Mj"),
                base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
            )
            
            # Create agent with system prompt
            self.agent = create_agent(
                model=model,
                tools=self.tools,
                system_prompt=self.get_system_prompt(),
                context_schema=RiskAgentContext,
            )
            
            if mcp_success:
                logger.info("✅ Risk Score Agent initialized with full MCP functionality!")
            else:
                logger.info("⚠️ Risk Score Agent initialized with limited functionality (no MCP tools)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            import traceback
            traceback.print_exc()
            # Ensure we have a fallback agent even on total failure
            if not hasattr(self, 'agent') or self.agent is None:
                try:
                    logger.info("Creating emergency fallback agent...")
                    from langchain_anthropic import ChatAnthropic
                    self.agent = ChatAnthropic(
                        model="claude-3-haiku-20240307",
                        api_key=os.environ.get("ANTHROPIC_API_KEY", "60b19768f0334766a3e3259590b14460.QTFX9bVQYgALL0Mj"),
                        base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
                    )
                    logger.info("⚠️ Emergency fallback agent created")
                except Exception as fallback_error:
                    logger.error(f"Even fallback agent creation failed: {fallback_error}")
            return False
    
    async def close(self):
        """Close the MCP client"""
        if self.mcp_client:
            self.mcp_client = None
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for risk score calculation"""
        return f"""You are an AP RISK SCORE CALCULATION AGENT.

**PRIMARY MISSION:**
1. Get network topology to discover ALL available Access Points
2. Calculate risk scores for EVERY available AP (not just one)
3. Update calculated scores in JSON storage

**AGENT 1 WORKFLOW:**

STEP 1: GET TOPOLOGY & DISCOVER APs
- OPTION A: Call get_network_topology_link_layer(network_id="{self.network_id}") to get complete network topology with ALL devices and their physical layout
  - Returns nodes (all devices including APs) and links (connections)
  - Provides wireless_devices list with all AP serials and names
- OPTION B: Call get_organization_devices(network_id="{self.network_id}") to get device list
  - Returns a list with ap_serials, ap_names, and device details
- Count total APs discovered
- Extract serial numbers for ALL APs

STEP 2: CALCULATE RISK SCORES FOR ALL APs
For EACH AP found in Step 1 (use parallel tool calls for efficiency):
  a) get_wireless_latency_history(network_id, device_serial) - get latency & jitter data
  b) get_wireless_usage_history(network_id, device_serial) - get retransmission & SNR data
  c) get_device_clients(device_serial) - get client load & auth failures

RISK SCORE FORMULA:
RISK_SCORE = 0.25 * latency_score + 
             0.20 * jitter_score + 
             0.20 * retrans_score + 
             0.15 * snr_score + 
             0.10 * load_score + 
             0.10 * auth_score

SCORING (each metric scored 0-100, higher = worse):
- Latency: <30ms=20, 30-60ms=50, 60-100ms=80, >100ms=100
- Jitter: <10ms=20, 10-20ms=50, 20-30ms=80, >30ms=100
- Retrans: <20/min=20, 20-35/min=50, 35-50/min=80, >50/min=100
- SNR: >25dB=20, 20-25dB=50, 15-20dB=80, <15dB=100
- Load: <20 clients=20, 20-40=50, 40-60=80, >60=100
- Auth Failures: <3/hr=20, 3-8/hr=50, 8-15/hr=80, >15/hr=100

RISK CLASSIFICATION:
- 0-20: Stable Network
- 21-40: Temporary Degradation
- 41-70: Sustained Degradation
- 71-100: Likely Failure

STEP 3: UPDATE JSON FOR ALL APs
For EACH AP, call update_risk_score with:
  - ap_serial: AP's serial number
  - risk_score: Calculated composite score (0-100)
  - risk_classification: Classification string
  - metrics: Dict with all individual scores and raw values
  - timestamp: Current ISO timestamp

**CRITICAL REQUIREMENTS:**
- Process ALL APs found (if 5 found, process all 5; if 10 found, process all 10)
- Use parallel tool calls for efficiency
- Update JSON for EVERY AP
- Report final count: "Processed X APs" where X = total from Step 1

**OUTPUT FORMAT:**
Summary of APs processed:
- Total APs discovered: X
- APs analyzed: X (must match)
- Risk classifications: Y Stable, Z Degraded, W Failing
- All scores updated in JSON"""
    
    async def calculate_risk_scores(self) -> Dict[str, Any]:
        """Run risk score calculation for all APs"""
        try:
            prompt = f"""**AGENT 1: RISK SCORE CALCULATION**

Network ID: {self.network_id}

**EXECUTE THE FOLLOWING WORKFLOW:**

STEP 1: GET TOPOLOGY & CHECK AVAILABLE APs
- OPTION A (RECOMMENDED): Call get_network_topology_link_layer(network_id="{self.network_id}")
  - Returns complete network layout with nodes and links
  - Extract wireless_devices list for all AP serials
- OPTION B: Call get_organization_devices(network_id="{self.network_id}")
  - Returns all devices with ap_serials list showing ALL APs
- Count total APs in the list
- List all AP serial numbers

STEP 2: CALCULATE RISK SCORES
For EACH AP serial discovered (use parallel calls):
- Get latency/jitter: get_wireless_latency_history(network_id, device_serial)
- Get usage/SNR: get_wireless_usage_history(network_id, device_serial)
- Get client load: get_device_clients(device_serial)
- Calculate composite risk score (0-100)
- Classify risk level

STEP 3: UPDATE JSON STORAGE
For EACH AP:
- Call update_risk_score(ap_serial, risk_score, risk_classification, metrics, timestamp)
- Include all metrics in JSON

STEP 4: REPORT SUMMARY
- Total APs discovered: X
- Total APs processed: X (must match)
- Risk breakdown by classification

**BEGIN EXECUTION NOW:**"""

            agent_context = RiskAgentContext(
                session_id=self.session_id,
                user_id=self.user_id,
                network_id=self.network_id,
                calculation_interval=self.calculation_interval
            )
            
            result = await self.agent.ainvoke(
                {"messages": [{"role": "user", "content": prompt}]},
                context=agent_context,
                config={
                    "recursion_limit": 25,
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
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "response": final_response
            }
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }
    
    async def continuous_calculation(self):
        """Run continuous risk score calculation"""
        print(f"🚀 Starting continuous risk calculation (interval: {self.calculation_interval}s)")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Calculation #{iteration}")
                
                result = await self.calculate_risk_scores()
                
                if result["success"]:
                    print("✅ Complete")
                else:
                    print(f"❌ Failed: {result.get('error')}")
                
                await asyncio.sleep(self.calculation_interval)
                
        except KeyboardInterrupt:
            print("\n⚠️ Stopped by user")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def single_calculation(self):
        """Perform a single risk score calculation"""
        result = await self.calculate_risk_scores()
        
        if result["success"]:
            print("\n" + result["response"])
        else:
            print(f"❌ Failed: {result.get('error')}")
        
        return result


# ============================================================================
# A2A Server for Inter-Agent Communication
# ============================================================================

# Storage path for risk scores
STORAGE_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "agent_data"
RISK_SCORES_FILE = STORAGE_DIR / "risk_scores.json"


def _load_risk_scores() -> Dict[str, Any]:
    """Load risk scores from JSON file"""
    try:
        if RISK_SCORES_FILE.exists():
            with open(RISK_SCORES_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading risk scores: {e}")
    return {}


if A2A_AVAILABLE:
    @agent(
        name="Risk Score Agent",
        description="Calculates and provides AP risk scores for failure prediction"
    )
    class RiskScoreA2AServer(A2AServer):
        """A2A Server for Risk Score Agent - enables inter-agent communication"""
        
        @skill(
            name="Get All Risk Scores",
            description="Get current risk scores for all APs"
        )
        def get_all_risk_scores(self) -> str:
            """Get all current risk scores"""
            data = _load_risk_scores()
            if not data:
                return json.dumps({"success": False, "message": "No risk data available"})
            
            summary = {}
            for serial, ap_data in data.items():
                current = ap_data.get("current", {})
                summary[serial] = {
                    "risk_score": current.get("risk_score", 0),
                    "risk_classification": current.get("risk_classification", "Unknown"),
                    "last_updated": ap_data.get("last_updated")
                }
            
            return json.dumps({
                "success": True,
                "ap_count": len(summary),
                "risk_scores": summary
            }, indent=2)
        
        @skill(
            name="Get AP Risk Score",
            description="Get risk score for a specific AP by serial number"
        )
        def get_ap_risk_score(self, ap_serial: str) -> str:
            """Get risk score for a specific AP"""
            data = _load_risk_scores()
            
            if ap_serial in data:
                ap_data = data[ap_serial]
                return json.dumps({
                    "success": True,
                    "ap_serial": ap_serial,
                    "current": ap_data.get("current", {}),
                    "last_updated": ap_data.get("last_updated")
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "message": f"No risk data for AP {ap_serial}"
                })
        
        @skill(
            name="Get At Risk APs",
            description="Get all APs with risk score above a threshold"
        )
        def get_at_risk_aps(self, min_risk_score: float = 40.0) -> str:
            """Get APs above risk threshold"""
            data = _load_risk_scores()
            
            at_risk = []
            for serial, ap_data in data.items():
                current = ap_data.get("current", {})
                score = current.get("risk_score", 0)
                if score >= min_risk_score:
                    at_risk.append({
                        "ap_serial": serial,
                        "risk_score": score,
                        "risk_classification": current.get("risk_classification", "Unknown"),
                        "metrics": current.get("metrics", {}),
                        "last_updated": ap_data.get("last_updated")
                    })
            
            # Sort by risk score descending
            at_risk.sort(key=lambda x: x["risk_score"], reverse=True)
            
            return json.dumps({
                "success": True,
                "threshold": min_risk_score,
                "count": len(at_risk),
                "at_risk_aps": at_risk
            }, indent=2)
        
        @skill(
            name="Get Risk History",
            description="Get historical risk scores for an AP"
        )
        def get_risk_history(self, ap_serial: str, limit: int = 10) -> str:
            """Get risk score history for an AP"""
            data = _load_risk_scores()
            
            if ap_serial in data:
                history = data[ap_serial].get("history", [])[-limit:]
                return json.dumps({
                    "success": True,
                    "ap_serial": ap_serial,
                    "history_count": len(history),
                    "history": history
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "message": f"No history for AP {ap_serial}"
                })
        
        def handle_task(self, task):
            """Handle incoming A2A tasks"""
            task_input = task.input.lower() if hasattr(task, 'input') else str(task).lower()
            
            # Parse task and route to appropriate skill
            if "all" in task_input and "risk" in task_input:
                return {"output": self.get_all_risk_scores()}
            elif "at risk" in task_input or "at-risk" in task_input:
                # Extract threshold if provided
                threshold = 40.0
                try:
                    import re
                    match = re.search(r'(\d+(?:\.\d+)?)', task_input)
                    if match:
                        threshold = float(match.group(1))
                except:
                    pass
                return {"output": self.get_at_risk_aps(threshold)}
            elif "history" in task_input:
                # Extract AP serial
                import re
                match = re.search(r'([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})', task_input.upper())
                if match:
                    return {"output": self.get_risk_history(match.group(1))}
                return {"output": json.dumps({"success": False, "message": "AP serial not found in request"})}
            elif any(x in task_input for x in ["serial", "ap "]):
                # Extract AP serial for specific query
                import re
                match = re.search(r'([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})', task_input.upper())
                if match:
                    return {"output": self.get_ap_risk_score(match.group(1))}
                return {"output": json.dumps({"success": False, "message": "AP serial not found in request"})}
            else:
                # Default: return all risk scores
                return {"output": self.get_all_risk_scores()}


def start_a2a_server(port: int = 5001):
    """Start the A2A server in a background thread"""
    if not A2A_AVAILABLE:
        logger.warning("A2A not available, skipping A2A server start")
        return None
    
    server_url = f"http://localhost:{port}"
    server = RiskScoreA2AServer(url=server_url)
    
    def run_a2a():
        logger.info(f"🌐 Starting Risk Score A2A Server on port {port}...")
        run_server(server, port=port)
    
    thread = threading.Thread(target=run_a2a, daemon=True)
    thread.start()
    logger.info(f"✅ Risk Score A2A Server started on http://localhost:{port}")
    return server


async def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    RISK SCORE CALCULATION AGENT (Agent 1)                    ║
║                                                                              ║
║  Calculates risk scores for all APs using parallel MCP tool calls           ║
║  Stores results in JSON for Network Monitoring Agent to consume             ║
║  A2A Server for inter-agent communication on port 5001                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Parse arguments
    mode = "single"
    interval = 10
    enable_a2a = True
    a2a_port = 5001
    
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
        elif args[i] == "--no-a2a":
            enable_a2a = False
        elif args[i] == "--a2a-port":
            if i + 1 < len(args):
                try:
                    a2a_port = int(args[i+1])
                    i += 1
                except ValueError:
                    pass
        elif args[i] in ["--help", "-h"]:
            print("\nUsage:")
            print("  python risk_score_agent.py                    - Single calculation")
            print("  python risk_score_agent.py --continuous [sec] - Continuous mode")
            print("  python risk_score_agent.py --no-a2a           - Disable A2A server")
            print("  python risk_score_agent.py --a2a-port [port]  - Set A2A port (default 5001)")
            print("  python risk_score_agent.py --help             - Show this help")
            print("\nExamples:")
            print("  python risk_score_agent.py --continuous 10    - Calculate every 10s")
            print("  python risk_score_agent.py --continuous 30 --a2a-port 5001")
            return
        i += 1
    
    # Start A2A server if enabled
    if enable_a2a and A2A_AVAILABLE:
        start_a2a_server(port=a2a_port)
        await asyncio.sleep(0.5)
    
    # Initialize agent
    print("Initializing agent...")
    agent = RiskScoreCalculationAgent(calculation_interval=interval)
    
    if not await agent.initialize():
        print("Failed to initialize agent")
        return
    
    print("✅ Agent ready")
    
    try:
        if mode == "continuous":
            await agent.continuous_calculation()
        else:
            await agent.single_calculation()
    finally:
        await agent.close()
        print("\n✅ Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
