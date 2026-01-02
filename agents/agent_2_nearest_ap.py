#!/usr/bin/env python3
"""
Agent 2: Nearest AP Calculation Agent

ARCHITECTURE:
- Agent orchestrates ONLY (NO calculations!)
- All distance/ranking math done by calculate_nearest_aps.py script
- Agent passes ALL parameters to MCP tool
- Results stored in nearest_aps.json

PURPOSE:
For each AP in the network:
1. Get AP topology (location, channel, floor)
2. Collect all other APs with their location data
3. Call calculate_nearest_aps tool (script does ALL math!)
4. Store nearest AP results in JSON

IMPORTANT:
- Agent does NO distance calculations
- Agent does NO Dijkstra algorithm
- Agent does NO ranking/scoring
- Agent ONLY orchestrates data collection and tool calls
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from python_a2a import A2AServer, run_server, Message, MessageRole, TextContent
import threading
import re

# OpenTelemetry imports for Phoenix tracing
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

# Load environment variables first
load_dotenv()

# Get project root - calculate from BASE_PATH or use file location
BASE_PATH = os.getenv('BASE_PATH')
if BASE_PATH:
    project_root = Path(BASE_PATH) / 'networkingAgent'
else:
    project_root = Path(__file__).parent.parent

# Add project root to path for imports
sys.path.insert(0, str(project_root))

# LangChain imports
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.callbacks import BaseCallbackHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("langchain_mcp_adapters").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.WARNING)
logger = logging.getLogger("nearest-ap-agent")


# Global A2A server instance
a2a_server_instance = None

# Global tracer for A2A
tracer = trace.get_tracer("agent-2-nearest-ap-a2a")


def handle_nearest_ap_request(text: str) -> str:
    """Handle A2A requests for nearest AP data"""
    with tracer.start_as_current_span("Agent2_receives_A2A_request") as span:
        span.set_attribute("source_agent", "unknown")
        span.set_attribute("target_agent", "Agent-2-NearestAP")
        span.set_attribute("agent", "agent-2")
        span.set_attribute("request_type", "a2a")
        span.set_attribute("communication.direction", "incoming")
        span.set_attribute("communication.protocol", "A2A")
        span.set_attribute("input.value", text)
        span.add_event("A2A Request Received", {"query": text})
        
        print(f"\n[A2A REQUEST] {text}")
        
        # Load nearest APs data
        nearest_file = project_root / "agent_data" / "nearest_aps.json"
        if not nearest_file.exists():
            return "No nearest AP data available yet. Please wait for calculation."
        
        with open(nearest_file, 'r') as f:
            data = json.load(f)
        
        # Extract AP serial from request
        serial_match = re.search(r'Q2XX-[A-Z0-9]{4}-[A-Z0-9]{4}', text)
        
        if serial_match:
            ap_serial = serial_match.group(0)
            span.set_attribute("ap_serial", ap_serial)
            
            if ap_serial in data:
                ap_data = data[ap_serial]
                nearest_aps = ap_data.get('nearest_aps', [])
                
                response = f"Nearest APs for {ap_serial} ({len(nearest_aps)} candidates):\n"
                for ap in nearest_aps[:5]:  # Top 5
                    response += f"  {ap.get('rank', '?')}. {ap.get('ap_name', 'Unknown')} ({ap.get('ap_serial', 'Unknown')}) - {ap.get('distance_meters', 0):.1f}m, RSSI: {ap.get('rssi_dbm', 0)}dBm\n"
                
                span.set_attribute("candidates_found", len(nearest_aps))
                span.set_attribute("output.value", response)
                span.add_event("A2A Response Sent", {"response": response, "candidates_found": len(nearest_aps)})
                print(f"[A2A RESPONSE] {len(nearest_aps)} candidates for {ap_serial}")
                return response
            else:
                return f"No data found for AP {ap_serial}"
        else:
            # Return summary of all APs
            response = f"Nearest AP data for {len(data)} APs available. Specify an AP serial (Q2XX-XXXX-XXXX) to get candidates."
            span.set_attribute("total_aps", len(data))
            span.set_attribute("output.value", response)
            span.add_event("A2A Response Sent", {"response": response, "total_aps": len(data)})
            print(f"[A2A RESPONSE] Summary of {len(data)} APs")
            return response


def start_a2a_server(port: int = 5002):
    """Start A2A server in background thread"""
    global a2a_server_instance
    
    class NearestAPA2AServer(A2AServer):
        def __init__(self, port):
            super().__init__(url=f"http://localhost:{port}")
            self.port = port
            self.request_count = 0
        
        def handle_message(self, message) -> Message:
            self.request_count += 1
            # Get text from message
            if hasattr(message.content, 'text'):
                text = message.content.text
            else:
                text = str(message.content)
            
            # Get response
            response_text = handle_nearest_ap_request(text)
            
            # Return Message object
            return Message(
                content=TextContent(text=response_text),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    a2a_server_instance = NearestAPA2AServer(port)
    print(f"\n[A2A] Starting server on port {port}...")
    thread = threading.Thread(
        target=lambda: run_server(a2a_server_instance, port=port),
        daemon=True
    )
    thread.start()
    import time
    time.sleep(2)  # Give server time to start
    print(f"[A2A] Server ready: http://localhost:{port}\n")




class ToolCallLogger(BaseCallbackHandler):
    """Callback to log all tool calls and responses"""
    
    def __init__(self):
        self.tool_calls = []
        self.calculate_calls = []
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        """Called when a tool starts"""
        tool_name = serialized.get("name", "Unknown")
        
        # Parse input if it's a string
        if isinstance(input_str, str):
            try:
                input_data = json.loads(input_str.replace("'", '"'))
            except:
                try:
                    input_data = eval(input_str) if input_str else {}
                except:
                    input_data = {"raw": input_str}
        elif isinstance(input_str, dict):
            input_data = input_str
        else:
            input_data = {"raw": str(input_str)}
        
        # Show all tool calls with inputs
        print(f"\n{'─'*100}")
        print(f"🔧 TOOL: {tool_name}")
        print(f"{'─'*100}")
        
        # Format inputs based on tool type
        if tool_name == "calculate_nearest_aps":
            source_serial = input_data.get('source_ap_serial', 'Unknown')
            source_name = input_data.get('source_ap_name', 'Unknown')
            all_aps = input_data.get('all_aps', [])
            
            print(f"📍 Source AP: {source_name} ({source_serial})")
            print(f"📊 Comparing against: {len(all_aps)} APs")
            
            self.calculate_calls.append({
                "source_serial": source_serial,
                "source_name": source_name,
                "candidate_count": len(all_aps)
            })
            
        elif tool_name == "get_device_clients":
            device_serial = input_data.get('device_serial', input_data.get('deviceSerial', 'Unknown'))
            print(f"📱 Device: {device_serial}")
            
        elif tool_name == "get_organization_devices":
            org_id = input_data.get('organization_id', input_data.get('organizationId', input_data.get('orgId', 'Unknown')))
            print(f"🏢 Organization: {org_id}")
            
        elif tool_name == "get_network_topology_link_layer":
            network_id = input_data.get('network_id', input_data.get('networkId', 'Unknown'))
            print(f"🌐 Network: {network_id}")
            
        elif tool_name == "update_nearest_aps":
            ap_serial = input_data.get('ap_serial', input_data.get('apSerial', 'Unknown'))
            nearest_count = len(input_data.get('nearest_aps', input_data.get('nearestAps', [])))
            print(f"💾 Storing for: {ap_serial}")
            print(f"📝 Nearest APs: {nearest_count}")
            
        elif tool_name == "get_organizations":
            print(f"🏢 Fetching organizations")
            
        elif tool_name == "get_organization_networks":
            org_id = input_data.get('organization_id', input_data.get('organizationId', input_data.get('orgId', 'Unknown')))
            print(f"🌐 Organization: {org_id}")
        
        else:
            # Show all parameters for debugging
            if isinstance(input_data, dict) and input_data:
                for key, value in list(input_data.items())[:3]:  # Show first 3 params
                    if isinstance(value, (str, int, float, bool)):
                        print(f"   {key}: {value}")
                if len(input_data) > 3:
                    print(f"   ... and {len(input_data) - 3} more parameters")
        
        self.tool_calls.append({
            "tool": tool_name,
            "input": input_data,
            "timestamp": datetime.now().isoformat()
        })
    
    def on_tool_end(self, output, **kwargs):
        """Called when a tool ends"""
        print(f"✅ Completed")
        if self.tool_calls:
            self.tool_calls[-1]["output"] = str(output)[:100] + "..."


async def run_calculation(mcp_client, tools, llm):
    """Run a single nearest AP calculation"""
    tool_logger = ToolCallLogger()
    
    # System prompt - STRICTLY GUIDE LLM TO ORCHESTRATE ONLY!
    system_prompt = """You are the Nearest AP Calculation Agent.

YOUR ROLE:
- Orchestrate ONLY - NO calculations, NO distance math, NO ranking!
- Collect AP topology data from the network
- Pass ALL parameters to the calculate_nearest_aps tool
- Store results in nearest_aps.json
- The script does ALL the distance/ranking/failover calculations!

STRICT WORKFLOW:
1. Get organization info (get_organizations)
2. Get network list (get_organization_networks)
3. Get AP topology for the network (get_network_topology_link_layer)
   - Extract ALL APs with: serial, name, lat, lng, floor, channel
4. Get device clients for each AP (client_count data)
5. FOR EACH AP in the topology:
   a. Call calculate_nearest_aps tool with:
      - source_ap_serial (REQUIRED)
      - source_ap_name (REQUIRED)
      - source_ap_lat (REQUIRED)
      - source_ap_lng (REQUIRED)
      - source_ap_floor (REQUIRED)
      - source_ap_channel (REQUIRED)
      - all_aps (REQUIRED - list of ALL other APs with location/channel data)
      - max_candidates (default 5)
   b. Store result using update_nearest_aps tool

CRITICAL RULES:
- NEVER calculate distance yourself
- NEVER run Dijkstra algorithm
- NEVER rank/score APs
- ALWAYS pass ALL 7+ required parameters to calculate_nearest_aps
- Tool does ALL the math - you just pass parameters!

VERIFICATION:
- Show each tool call with inputs/outputs in bordered boxes
- Confirm ALL APs processed
- Confirm results stored in nearest_aps.json

Begin the workflow now!"""
    
    # Create agent
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt
    )
    
    # Run the agent
    logger.info("\nExecuting Nearest AP calculation workflow...")
    logger.info("="*80)
    
    prompt = "Calculate nearest APs for ALL access points in the network. For each AP, find the 5 nearest APs using distance and topology analysis. Store all results in nearest_aps.json."
    
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config={
            "recursion_limit": 50,
            "callbacks": [tool_logger]
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
    
    logger.info("\n" + "="*80)
    logger.info("Agent execution completed!")
    logger.info("="*80)
    
    # Print calculation summary table
    print("\n" + "="*100)
    print("📊 NEAREST AP CALCULATION SUMMARY")
    print("="*100)
    print(f"\n{'AP Serial':<20} {'AP Name':<15} {'Candidates':<15} {'Status':<20}")
    print("-"*100)
    
    for calc in tool_logger.calculate_calls:
        print(f"{calc['source_serial']:<20} {calc['source_name']:<15} {calc['candidate_count']:<15} {'✅ Calculated':<20}")
    
    print("-"*100)
    print(f"Total APs Processed: {len(tool_logger.calculate_calls)}")
    print("="*100)
    
    # Show stored results
    agent_data_dir = project_root / "agent_data"
    nearest_aps_file = agent_data_dir / "nearest_aps.json"
    
    if nearest_aps_file.exists():
        with open(nearest_aps_file, 'r') as f:
            stored_data = json.load(f)
        
        print("\n" + "="*100)
        print("📍 NEAREST APs FOUND (RESULTS)")
        print("="*100)
        
        for ap_serial, ap_data in stored_data.items():
            ap_name = ap_data.get('ap_serial', ap_serial)
            nearest = ap_data.get('nearest_aps', [])
            
            print(f"\n🔹 {ap_serial}:")
            print(f"   {'Rank':<6} {'AP Name':<15} {'Distance (m)':<15} {'RSSI (dBm)':<15} {'Score':<10}")
            print(f"   {'-'*70}")
            
            for ap in nearest[:5]:  # Show top 5
                rank = ap.get('rank', '-')
                name = ap.get('ap_name', 'Unknown')
                dist = ap.get('distance_meters', 0)
                rssi = ap.get('rssi_dbm', 0)
                score = ap.get('composite_score', 0)
                print(f"   {rank:<6} {name:<15} {dist:<15.1f} {rssi:<15} {score:<10}")
        
        print("\n" + "="*100)
        print(f"✅ Results saved to: {nearest_aps_file}")
        print("="*100)


async def main():
    """Run Nearest AP Calculation Agent"""
    
    # Initialize Phoenix tracing for A2A
    resource = Resource.create({"service.name": "agent-2-nearest-ap-a2a"})
    tracer_provider = trace_sdk.TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(endpoint="http://127.0.0.1:6006/v1/traces")
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)
    print("✅ Phoenix tracing enabled for A2A: http://localhost:6006\n")
    
    # Parse command line arguments
    mode = "single"
    interval = 10  # Default 10 seconds
    
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
        elif args[i] in ["--help", "-h"]:
            print("\nUsage:")
            print("  python agent_2_nearest_ap.py                    - Single calculation")
            print("  python agent_2_nearest_ap.py --continuous [sec] - Continuous mode")
            print("  python agent_2_nearest_ap.py --help             - Show this help")
            print("\nExamples:")
            print("  python agent_2_nearest_ap.py --continuous 60    - Calculate every 60s")
            print("  python agent_2_nearest_ap.py --continuous 120   - Calculate every 120s")
            return
        i += 1
    
    logger.info("Starting Nearest AP Calculation Agent (Agent 2)")
    logger.info("="*80)
    
    # Initialize MCP client using MultiServerMCPClient
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    server_path = os.path.join(script_dir, "server", "meraki_server.py")
    
    logger.info(f"Connecting to MCP server: {server_path}")
    
    mcp_client = MultiServerMCPClient(
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
    
    try:
        # Get tools (no context manager needed)
        tools = await mcp_client.get_tools()
        logger.info(f"✅ Loaded {len(tools)} MCP tools")
        
        # Start A2A server
        start_a2a_server(port=5002)
        
        # Initialize LLM (GLM-4.5 via Anthropic SDK)
        llm = init_chat_model(
            model="glm-4.5",
            model_provider="anthropic",  # Using OpenAI-compatible API
            temperature=0,
            max_tokens=1024,
            timeout=60,
            max_retries=2,
            api_key=os.environ.get("ANTHROPIC_API_KEY", "60b19768f0334766a3e3259590b14460.QTFX9bVQYgALL0Mj"),
            base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
        )
        
        # Run in selected mode
        if mode == "continuous":
            print(f"🚀 Starting continuous nearest AP calculation (interval: {interval}s)")
            iteration = 0
            
            try:
                while True:
                    iteration += 1
                    print(f"\n{'='*80}")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Calculation #{iteration}")
                    print(f"{'='*80}")
                    
                    await run_calculation(mcp_client, tools, llm)
                    
                    print(f"\n⏳ Next calculation in {interval}s...")
                    await asyncio.sleep(interval)
                    
            except KeyboardInterrupt:
                print("\n⚠️ Stopped by user")
        else:
            # Single calculation
            await run_calculation(mcp_client, tools, llm)
        
    except Exception as e:
        logger.error(f"Error during agent execution: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        mcp_client = None
        logger.info("MCP client cleaned up")


if __name__ == "__main__":
    asyncio.run(main())
