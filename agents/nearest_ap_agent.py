#!/usr/bin/env python3
"""
Nearest AP Recommendation Agent (Agent 2)
Calculates and ranks nearest Access Points for failover recommendations.

Features:
- Parallel MCP tool calling for efficient topology data collection
- Ranks APs by: Distance (30%), RSSI (25%), Client Load (20%), 
  Channel Overlap (15%), Same Floor (10%)
- Stores results in JSON for Network Monitoring Agent to consume
- A2A Server for inter-agent communication
- Runs continuously with configurable interval
"""

import asyncio
import json
import logging
import os
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
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
    logging.warning("python-a2a not installed. A2A server features will be disabled. Install with: pip install python-a2a")

# Load environment variables
load_dotenv()

# Langfuse configuration
os.environ["LANGFUSE_PUBLIC_KEY"] = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-05aedc22-20c5-43f0-b9bf-4aa500d749fe")
os.environ["LANGFUSE_SECRET_KEY"] = os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-864cdd54-cd46-42db-aacf-69233345b37e")
os.environ["LANGFUSE_BASE_URL"] = os.getenv("LANGFUSE_BASE_URL", "http://localhost:3000")

# Import tracing module
from core.tracing import (
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
logger = logging.getLogger("nearest-ap-agent")


@dataclass
class NearestAPAgentContext:
    """Context schema for the nearest AP recommendation agent"""
    session_id: str
    user_id: str
    network_id: str
    calculation_interval: int


class NearestAPRecommendationAgent:
    """
    Agent 2: Nearest AP Recommendation Agent
    
    Calculates and ranks nearest APs for each AP using topology data.
    Uses parallel tool calls for efficient data collection.
    Stores results in JSON for the Network Monitoring Agent to consume.
    """
    
    def __init__(self, calculation_interval: int = 30):
        self.mcp_client: Optional[MultiServerMCPClient] = None
        self.agent = None
        self.tools = None
        
        # Configuration
        self.calculation_interval = calculation_interval
        self.session_id = create_session_id()
        self.user_id = "nearest-ap-agent"
        self.network_id = "L_3947405073390239794"
        
        # Ranking weights for AP selection
        self.ranking_weights = {
            "distance": 0.30,      # Closer is better
            "rssi": 0.25,          # Higher signal strength is better
            "client_load": 0.20,   # Lower client count is better
            "channel_overlap": 0.15,  # No overlap is better
            "same_floor": 0.10     # Same floor preferred
        }
        
        logger.info(f"🔗 Nearest AP Agent Session: {self.session_id}")
    
    async def initialize(self) -> bool:
        """Initialize the MCP client and agent"""
        try:
            logger.info("Initializing Nearest AP Recommendation Agent...")
            
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
                logger.info("Loading MCP tools...")
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
                max_tokens=4096,
                timeout=120,
                max_retries=2,
                api_key=os.environ.get("ANTHROPIC_API_KEY", "60b19768f0334766a3e3259590b14460.QTFX9bVQYgALL0Mj"),
                base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
            )
            
            # Create agent with system prompt
            self.agent = create_agent(
                model=model,
                tools=self.tools,
                system_prompt=self.get_system_prompt(),
                context_schema=NearestAPAgentContext,
            )
            
            if mcp_success:
                logger.info("✅ Nearest AP Agent initialized with full MCP functionality!")
            else:
                logger.info("⚠️ Nearest AP Agent initialized with limited functionality (no MCP tools)")
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
            logger.info("Closing MCP client...")
            self.mcp_client = None
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for nearest AP calculation"""
        return f"""You are a NEAREST AP RECOMMENDATION AGENT for wireless networks.

**PRIMARY MISSION:**
Calculate and rank the nearest Access Points for EACH AP in the network.
Store failover recommendations in JSON for the Network Monitoring Agent to consume.

**RANKING FORMULA (Composite Score 0-100, higher = better):**
COMPOSITE_SCORE = 
  {self.ranking_weights['distance']} * distance_score +
  {self.ranking_weights['rssi']} * rssi_score +
  {self.ranking_weights['client_load']} * load_score +
  {self.ranking_weights['channel_overlap']} * overlap_score +
  {self.ranking_weights['same_floor']} * floor_score

**SCORING CRITERIA (0-100 scale):**

1. **Distance Score** (30% weight):
   - < 10 meters → 100 (Excellent)
   - 10-20 meters → 80 (Good)
   - 20-35 meters → 60 (Acceptable)
   - 35-50 meters → 40 (Marginal)
   - > 50 meters → 20 (Poor)

2. **RSSI Score** (25% weight):
   - > -50 dBm → 100 (Excellent)
   - -50 to -60 dBm → 80 (Good)
   - -60 to -70 dBm → 60 (Acceptable)
   - -70 to -80 dBm → 40 (Marginal)
   - < -80 dBm → 20 (Poor)

3. **Client Load Score** (20% weight):
   - < 10 clients → 100 (Excellent)
   - 10-20 clients → 80 (Good)
   - 20-35 clients → 60 (Acceptable)
   - 35-50 clients → 40 (Marginal)
   - > 50 clients → 20 (Overloaded)

4. **Channel Overlap Score** (15% weight):
   - No overlap → 100 (Best)
   - Overlap → 0 (Avoid)

5. **Same Floor Score** (10% weight):
   - Same floor → 100 (Preferred)
   - Different floor → 50 (Acceptable)

**EXECUTION STEPS (USE PARALLEL TOOL CALLS):**

1. **Discover all APs** - Call get_wireless_health to find all AP serials in the network

2. **Get topology for ALL APs in PARALLEL:**
   For each AP, call get_ap_topology to get nearby APs with:
   - Distance in meters
   - Signal strength (RSSI)
   - Channel overlap status
   - Floor information
   
   **PARALLEL CALL EXAMPLE:**
   - get_ap_topology(network_id="...", ap_serial="AP1")
   - get_ap_topology(network_id="...", ap_serial="AP2")
   - get_ap_topology(network_id="...", ap_serial="AP3")
   (All in same batch)

3. **Get client load for each nearby AP in PARALLEL:**
   For each nearby AP discovered, call get_device_clients to check current load
   
   **PARALLEL CALL EXAMPLE:**
   - get_device_clients(device_serial="NEARBY1")
   - get_device_clients(device_serial="NEARBY2")
   (All in same batch)

4. **Calculate composite scores** for each nearby AP using the formula

5. **Rank and store results** by calling update_nearest_aps for EACH source AP:
   - ap_serial: Source AP's serial number
   - nearest_aps: Array of ranked nearby APs with:
     - ap_serial: Nearby AP serial
     - ap_name: Nearby AP name
     - distance_meters: Distance from source
     - rssi_dbm: Signal strength
     - client_load: Current client count
     - channel_overlap: Boolean
     - same_floor: Boolean
     - composite_score: Calculated score (0-100)
     - rank: Position (1 = best)

**DATA FORMAT FOR update_nearest_aps:**
```json
{{
  "ap_serial": "SOURCE-AP-SERIAL",
  "nearest_aps": [
    {{
      "ap_serial": "NEARBY-AP-1",
      "ap_name": "AP-01",
      "distance_meters": 15.5,
      "rssi_dbm": -55,
      "client_load": 12,
      "channel_overlap": false,
      "same_floor": true,
      "composite_score": 82.5,
      "rank": 1
    }},
    {{
      "ap_serial": "NEARBY-AP-2",
      "ap_name": "AP-02",
      "distance_meters": 22.0,
      "rssi_dbm": -62,
      "client_load": 8,
      "channel_overlap": true,
      "same_floor": true,
      "composite_score": 68.0,
      "rank": 2
    }}
  ]
}}
```

**OUTPUT FORMAT:**
After processing all APs, provide a summary:
- Total APs processed
- Average number of failover candidates per AP
- Any APs with limited failover options (< 2 candidates)

**IMPORTANT:**
- Always use PARALLEL tool calls when possible for efficiency
- Rank ALL nearby APs, not just the best one
- Store complete data including all metrics
- Top 5 candidates per AP is ideal
- Handle APs with no nearby options gracefully"""
    
    async def calculate_nearest_aps(self) -> Dict[str, Any]:
        """Calculate nearest AP recommendations for all APs"""
        
        with TracingContext(
            name="nearest-ap-calculation",
            session_id=self.session_id,
            user_id=self.user_id,
            tags=["nearest-ap-agent", "topology"],
            metadata={"network_id": self.network_id}
        ) as ctx:
            try:
                logger.info("🗺️ Calculating nearest APs for all devices...")
                
                prompt = f"""**EXECUTE NEAREST AP CALCULATION NOW:**

Network ID: {self.network_id}

1. Call get_wireless_health to discover all APs in the network

2. For EACH AP, use PARALLEL tool calls to get topology:
   - get_ap_topology(network_id="{self.network_id}", ap_serial="<AP_SERIAL>")
   Do this for ALL APs in parallel!

3. For each nearby AP discovered, get client load in PARALLEL:
   - get_device_clients(device_serial="<NEARBY_AP_SERIAL>")

4. Calculate composite scores using the ranking formula

5. Call update_nearest_aps for EACH source AP with ranked candidates

6. Provide summary of all APs processed

**START CALCULATION - USE PARALLEL TOOL CALLS FOR EFFICIENCY:**"""

                if ctx.span:
                    ctx.span.update(input={"prompt": prompt})
                
                agent_context = NearestAPAgentContext(
                    session_id=self.session_id,
                    user_id=self.user_id,
                    network_id=self.network_id,
                    calculation_interval=self.calculation_interval
                )
                
                trace_id = ctx.trace_id
                
                result = await self.agent.ainvoke(
                    {"messages": [{"role": "user", "content": prompt}]},
                    context=agent_context,
                    config={
                        "run_name": "nearest-ap-calculation",
                        "tags": ["topology", "parallel-tools"],
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
                
                logger.info("✅ Nearest AP calculation complete")
                
                return {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "session_id": self.session_id,
                    "response": final_response
                }
                
            except Exception as e:
                logger.error(f"Error calculating nearest APs: {e}")
                import traceback
                traceback.print_exc()
                if ctx.span:
                    ctx.span.update(output={"error": str(e), "success": False})
                return {
                    "success": False,
                    "error": str(e),
                    "session_id": self.session_id
                }
    
    async def continuous_calculation(self):
        """Run continuous nearest AP calculation"""
        logger.info(f"🚀 Starting continuous topology calculation (interval: {self.calculation_interval}s)")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"Topology Calculation #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info(f"{'='*60}")
                
                result = await self.calculate_nearest_aps()
                
                if result["success"]:
                    logger.info(f"🗺️ Calculation complete")
                    print(result["response"][:500] + "..." if len(result["response"]) > 500 else result["response"])
                else:
                    logger.error(f"❌ Calculation failed: {result.get('error')}")
                
                logger.info(f"⏳ Next calculation in {self.calculation_interval}s...")
                await asyncio.sleep(self.calculation_interval)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️ Topology calculation stopped by user")
        except Exception as e:
            logger.error(f"❌ Calculation error: {e}")
    
    async def single_calculation(self):
        """Perform a single nearest AP calculation"""
        logger.info("🗺️ Performing single topology calculation...")
        
        result = await self.calculate_nearest_aps()
        
        if result["success"]:
            print("\n" + result["response"])
        else:
            logger.error(f"❌ Calculation failed: {result.get('error')}")
        
        return result


# ============================================================================
# A2A Server for Inter-Agent Communication
# ============================================================================

# Storage path for nearest APs data
STORAGE_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "agent_data"
NEAREST_APS_FILE = STORAGE_DIR / "nearest_aps.json"


def _load_nearest_aps() -> Dict[str, Any]:
    """Load nearest APs data from JSON file"""
    try:
        if NEAREST_APS_FILE.exists():
            with open(NEAREST_APS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading nearest APs: {e}")
    return {}


if A2A_AVAILABLE:
    @agent(
        name="Nearest AP Agent",
        description="Provides nearest AP recommendations for failover scenarios"
    )
    class NearestAPA2AServer(A2AServer):
        """A2A Server for Nearest AP Agent - enables inter-agent communication"""
        
        @skill(
            name="Get All Nearest APs",
            description="Get nearest AP data for all APs in the network"
        )
        def get_all_nearest_aps(self) -> str:
            """Get nearest APs for all source APs"""
            data = _load_nearest_aps()
            if not data:
                return json.dumps({"success": False, "message": "No topology data available"})
            
            summary = {}
            for serial, ap_data in data.items():
                nearest = ap_data.get("nearest_aps", [])
                summary[serial] = {
                    "candidate_count": len(nearest),
                    "top_candidate": nearest[0] if nearest else None,
                    "last_updated": ap_data.get("last_updated")
                }
            
            return json.dumps({
                "success": True,
                "ap_count": len(summary),
                "topology_summary": summary
            }, indent=2)
        
        @skill(
            name="Get Nearest APs for AP",
            description="Get nearest AP candidates for a specific AP serial"
        )
        def get_nearest_for_ap(self, ap_serial: str) -> str:
            """Get nearest APs for a specific source AP"""
            data = _load_nearest_aps()
            
            if ap_serial in data:
                ap_data = data[ap_serial]
                return json.dumps({
                    "success": True,
                    "source_ap": ap_serial,
                    "nearest_aps": ap_data.get("nearest_aps", []),
                    "last_updated": ap_data.get("last_updated")
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "message": f"No topology data for AP {ap_serial}"
                })
        
        @skill(
            name="Get Failover Recommendation",
            description="Get the best failover AP recommendation for a specific AP"
        )
        def get_failover_recommendation(self, ap_serial: str) -> str:
            """Get the best failover candidate for an AP"""
            data = _load_nearest_aps()
            
            if ap_serial in data:
                nearest = data[ap_serial].get("nearest_aps", [])
                if nearest:
                    # Return the top-ranked candidate
                    best = nearest[0]
                    return json.dumps({
                        "success": True,
                        "source_ap": ap_serial,
                        "failover_recommendation": {
                            "target_ap": best.get("ap_serial"),
                            "target_name": best.get("ap_name"),
                            "distance_meters": best.get("distance_meters"),
                            "composite_score": best.get("composite_score"),
                            "client_load": best.get("client_load"),
                            "same_floor": best.get("same_floor")
                        },
                        "alternative_count": len(nearest) - 1,
                        "alternatives": [a.get("ap_serial") for a in nearest[1:4]]
                    }, indent=2)
                else:
                    return json.dumps({
                        "success": False,
                        "message": f"No failover candidates for AP {ap_serial}"
                    })
            else:
                return json.dumps({
                    "success": False,
                    "message": f"No topology data for AP {ap_serial}"
                })
        
        @skill(
            name="Get APs with Limited Failover",
            description="Get APs that have fewer than the specified number of failover options"
        )
        def get_limited_failover_aps(self, min_candidates: int = 2) -> str:
            """Get APs with limited failover options"""
            data = _load_nearest_aps()
            
            limited = []
            for serial, ap_data in data.items():
                candidate_count = len(ap_data.get("nearest_aps", []))
                if candidate_count < min_candidates:
                    limited.append({
                        "ap_serial": serial,
                        "candidate_count": candidate_count,
                        "candidates": [a.get("ap_serial") for a in ap_data.get("nearest_aps", [])],
                        "last_updated": ap_data.get("last_updated")
                    })
            
            return json.dumps({
                "success": True,
                "threshold": min_candidates,
                "count": len(limited),
                "limited_failover_aps": limited
            }, indent=2)
        
        def handle_task(self, task):
            """Handle incoming A2A tasks"""
            task_input = task.input.lower() if hasattr(task, 'input') else str(task).lower()
            
            # Parse task and route to appropriate skill
            if "failover" in task_input and ("recommend" in task_input or "best" in task_input):
                # Extract AP serial
                import re
                match = re.search(r'([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})', task_input.upper())
                if match:
                    return {"output": self.get_failover_recommendation(match.group(1))}
                return {"output": json.dumps({"success": False, "message": "AP serial not found in request"})}
            
            elif "limited" in task_input or "few" in task_input:
                # Extract threshold if provided
                threshold = 2
                try:
                    import re
                    match = re.search(r'(\d+)', task_input)
                    if match:
                        threshold = int(match.group(1))
                except:
                    pass
                return {"output": self.get_limited_failover_aps(threshold)}
            
            elif "all" in task_input:
                return {"output": self.get_all_nearest_aps()}
            
            elif any(x in task_input for x in ["serial", "ap ", "nearest"]):
                # Extract AP serial for specific query
                import re
                match = re.search(r'([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})', task_input.upper())
                if match:
                    return {"output": self.get_nearest_for_ap(match.group(1))}
                return {"output": json.dumps({"success": False, "message": "AP serial not found in request"})}
            
            else:
                # Default: return all nearest APs
                return {"output": self.get_all_nearest_aps()}


def start_a2a_server(port: int = 5002):
    """Start the A2A server in a background thread"""
    if not A2A_AVAILABLE:
        logger.warning("A2A not available, skipping A2A server start")
        return None
    
    server_url = f"http://localhost:{port}"
    server = NearestAPA2AServer(url=server_url)
    
    def run_a2a():
        logger.info(f"🌐 Starting Nearest AP A2A Server on port {port}...")
        run_server(server, port=port)
    
    thread = threading.Thread(target=run_a2a, daemon=True)
    thread.start()
    logger.info(f"✅ Nearest AP A2A Server started on http://localhost:{port}")
    return server


async def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 NEAREST AP RECOMMENDATION AGENT (Agent 2)                    ║
║                                                                              ║
║  Calculates and ranks nearest APs for failover using parallel tool calls    ║
║  Stores results in JSON for Network Monitoring Agent to consume             ║
║  A2A Server for inter-agent communication on port 5002                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Parse arguments
    mode = "single"
    interval = 30
    enable_a2a = True
    a2a_port = 5002
    
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
            print("  python nearest_ap_agent.py                    - Single calculation")
            print("  python nearest_ap_agent.py --continuous [sec] - Continuous mode")
            print("  python nearest_ap_agent.py --no-a2a           - Disable A2A server")
            print("  python nearest_ap_agent.py --a2a-port [port]  - Set A2A port (default 5002)")
            print("  python nearest_ap_agent.py --help             - Show this help")
            print("\nExamples:")
            print("  python nearest_ap_agent.py --continuous 30    - Calculate every 30s")
            print("  python nearest_ap_agent.py --continuous 60 --a2a-port 5002")
            return
        i += 1
    
    # Verify Langfuse
    if verify_langfuse_connection():
        print("✅ Langfuse connected")
    else:
        print("⚠️ Langfuse not available")
    
    # Start A2A server if enabled
    if enable_a2a and A2A_AVAILABLE:
        start_a2a_server(port=a2a_port)
        await asyncio.sleep(1)  # Wait for server to start
    
    # Initialize agent
    agent = NearestAPRecommendationAgent(calculation_interval=interval)
    
    if not await agent.initialize():
        logger.error("Failed to initialize agent")
        return
    
    try:
        if mode == "continuous":
            await agent.continuous_calculation()
        else:
            await agent.single_calculation()
    finally:
        await agent.close()
        logger.info("✅ Nearest AP Agent shut down")


if __name__ == "__main__":
    asyncio.run(main())
