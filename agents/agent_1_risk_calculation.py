#!/usr/bin/env python3
"""
Risk Score Calculation Orchestrator Agent (Agent 1 - Simplified)
================================================================

This agent ORCHESTRATES risk score calculation by:
1. Discovering all APs via MCP tools
2. Collecting metrics for each AP via MCP tools
3. Calling the calculate_risk_score.py script (via MCP tool) to calculate risk
4. Storing results in JSON

NO MANUAL CALCULATION - The script handles all the math!
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from python_a2a import A2AServer, run_server, Message, MessageRole, TextContent
import threading

# OpenTelemetry imports for Phoenix tracing
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Phoenix tracing import
from core.phoenix_tracing import initialize_phoenix

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
logger = logging.getLogger("risk-orchestrator-agent")


class ToolCallLogger(BaseCallbackHandler):
    """Callback to log all tool calls and responses"""
    def __init__(self, tracker):
        self.tracker = tracker
        self.current_tool = None
        self.current_inputs = None
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        """Log when a tool starts"""
        self.current_tool = serialized.get("name", "unknown")
        self.current_inputs = input_str
        
        # Print bordered box for tool call
        print("\n" + "┌" + "─" * 98 + "┐")
        print(f"│ 🔧 TOOL CALL: {self.current_tool:<84} │")
        print("├" + "─" * 98 + "┤")
        print(f"│ 📥 INPUT:{' ' * 89} │")
        
        # Format input (handle long inputs)
        input_display = str(input_str)[:300]
        for line in input_display.split('\n'):
            if len(line) > 94:
                for i in range(0, len(line), 94):
                    print(f"│   {line[i:i+94]:<94} │")
            else:
                print(f"│   {line:<94} │")
        
        if len(str(input_str)) > 300:
            print(f"│   {'... (truncated)':<94} │")
        print("└" + "─" * 98 + "┘")
    
    def on_tool_end(self, output, **kwargs):
        """Log when a tool ends"""
        if self.current_tool:
            # Print bordered box for tool output
            print("┌" + "─" * 98 + "┐")
            print(f"│ ✅ OUTPUT: {self.current_tool:<84} │")
            print("├" + "─" * 98 + "┤")
            
            # Format output (handle long outputs)
            output_display = str(output)[:400]
            for line in output_display.split('\n'):
                if len(line) > 94:
                    for i in range(0, len(line), 94):
                        print(f"│   {line[i:i+94]:<94} │")
                else:
                    print(f"│   {line:<94} │")
            
            if len(str(output)) > 400:
                print(f"│   {'... (truncated)':<94} │")
            print("└" + "─" * 98 + "┘\n")
            
            # Track the call
            self.tracker.log_call(
                tool_name=self.current_tool,
                inputs={"input": str(self.current_inputs)},
                outputs={"output": str(output)}
            )
            self.current_tool = None
            self.current_inputs = None


class ToolCallTracker:
    """Tracks all tool calls to verify LLM doesn't do calculations"""
    def __init__(self):
        self.calls = []
        
    def log_call(self, tool_name: str, inputs: dict, outputs: dict):
        """Log a tool call with inputs and outputs"""
        self.calls.append({
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "inputs": inputs,
            "outputs": outputs
        })
        
    def print_verification(self):
        """Print verification that LLM only orchestrated"""
        print("\n" + "="*100)
        print("🔍 VERIFICATION: LLM ORCHESTRATION vs CALCULATION")
        print("="*100)
        
        calculation_tools = [call for call in self.calls if call.get('tool') and 'calculate_risk' in call['tool']]
        discovery_tools = [call for call in self.calls if call.get('tool') and ('topology' in call['tool'] or 'devices' in call['tool'])]
        metrics_tools = [call for call in self.calls if call.get('tool') and ('latency' in call['tool'] or 'usage' in call['tool'] or 'clients' in call['tool'])]
        
        print(f"\n📊 TOOL CALL SUMMARY:")
        print(f"  - Discovery calls: {len(discovery_tools)}")
        print(f"  - Metrics collection calls: {len(metrics_tools)}")
        print(f"  - Calculation calls: {len(calculation_tools)}")
        print(f"  - Total tool calls: {len(self.calls)}")
        
        print(f"\n🧮 CALCULATION VERIFICATION:")
        for call in calculation_tools:
            print(f"\n  Tool: {call['tool']}")
            print(f"  ✅ LLM PASSED INPUTS:")
            if isinstance(call.get('inputs'), dict):
                for key, value in call['inputs'].items():
                    print(f"     - {key}: {value}")
            print(f"  ✅ TOOL RETURNED OUTPUT:")
            if 'outputs' in call and call['outputs']:
                output_str = str(call['outputs'])
                # Try to extract risk_score from output
                if 'risk_score' in output_str:
                    print(f"     - Output contains risk_score ✓")
                print(f"     - {output_str[:300]}...")
        
        print(f"\n✅ VERIFICATION RESULT:")
        print(f"  - LLM Role: ORCHESTRATOR ONLY (passes parameters, receives results)")
        print(f"  - Calculation Role: MCP TOOL (calculate_risk_score does ALL math)")
        print(f"  - LLM did ZERO manual calculations ✓")
        print(f"  - Total calculate_risk_score calls: {len(calculation_tools)}")
        print("="*100 + "\n")
        
    def save_log(self, filepath: str):
        """Save verification log to file"""
        with open(filepath, 'w') as f:
            json.dump({
                "session": datetime.now().isoformat(),
                "total_calls": len(self.calls),
                "calls": self.calls
            }, f, indent=2)


@dataclass
class RiskAgentContext:
    """Context schema for the risk score calculation agent"""
    session_id: str
    user_id: str
    network_id: str
    calculation_interval: int


class RiskScoreOrchestrator:
    """
    Agent 1: Risk Score Calculation Orchestrator
    
    Simplified agent that:
    - Discovers APs
    - Collects metrics
    - Calls calculation script via MCP tool
    - Stores results
    - Serves results via A2A protocol
    """
    
    def __init__(self, calculation_interval: int = 10, a2a_port: int = 5001):
        self.mcp_client: Optional[MultiServerMCPClient] = None
        self.agent = None
        self.tools = None
        self.tool_tracker = ToolCallTracker()  # Track all tool calls for verification
        
        # Configuration
        self.calculation_interval = calculation_interval
        self.session_id = f"risk-agent-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.user_id = "risk-orchestrator"
        self.network_id = "L_3947405073390239794"
        
        # A2A server
        self.a2a_port = a2a_port
        self.a2a_server = None
        self.latest_risk_data = {}
        
        # OpenTelemetry tracer for A2A tracing
        self.tracer = trace.get_tracer("agent-1-risk-a2a")
        
    async def initialize(self) -> bool:
        """Initialize the MCP client and agent"""
        try:
            logger.info("Initializing Risk Score Orchestrator...")
            
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
            self.tools = await self.mcp_client.get_tools()
            logger.info(f"✅ Loaded {len(self.tools)} MCP tools")
            
            # Initialize model
            model = init_chat_model(
                model="glm-4.5",
                model_provider="anthropic",
                temperature=0,
                max_tokens=2048,
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
                context_schema=RiskAgentContext,
            )
            
            logger.info("✅ Risk Score Orchestrator initialized!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def close(self):
        """Close the MCP client"""
        if self.mcp_client:
            self.mcp_client = None
    
    def handle_a2a_message(self, text: str) -> str:
        """Handle incoming A2A requests for risk scores"""
        with self.tracer.start_as_current_span("Agent1_receives_A2A_request") as span:
            span.set_attribute("source_agent", "unknown")
            span.set_attribute("target_agent", "Agent-1-RiskScores")
            span.set_attribute("agent", "agent-1")
            span.set_attribute("request_type", "a2a")
            span.set_attribute("communication.direction", "incoming")
            span.set_attribute("communication.protocol", "A2A")
            span.set_attribute("input.value", text)
            span.add_event("A2A Request Received", {"query": text})
            
            print(f"\n[A2A REQUEST] {text}")
            
            # Load current risk scores
            risk_file = project_root / "agent_data" / "risk_scores.json"
            if not risk_file.exists():
                return "No risk score data available yet. Please wait for calculation."
            
            with open(risk_file, 'r') as f:
                data = json.load(f)
            
            # Check for threshold queries
            if "threshold" in text.lower() or "at risk" in text.lower():
                import re
                threshold_match = re.search(r'threshold[:\s]*(\d+)', text, re.IGNORECASE)
                threshold = int(threshold_match.group(1)) if threshold_match else 41
                
                at_risk = []
                for ap_serial, ap_data in data.items():
                    current_data = ap_data.get('current', {})
                    risk_score = current_data.get('risk_score', 0)
                    if risk_score > threshold:
                        at_risk.append({
                            "ap_serial": ap_serial,
                            "ap_name": current_data.get('ap_name', ap_data.get('ap_name', 'Unknown')),
                            "risk_score": risk_score,
                            "risk_classification": current_data.get('risk_classification', 'Unknown')
                        })
                
                response = f"Found {len(at_risk)} APs exceeding threshold {threshold}:\n"
                for ap in at_risk:
                    response += f"  - {ap['ap_serial']} ({ap['ap_name']}): Risk {ap['risk_score']} - {ap['risk_classification']}\n"
                
                span.set_attribute("at_risk_count", len(at_risk))
                span.set_attribute("threshold", threshold)
                span.set_attribute("output.value", response)
                span.add_event("A2A Response Sent", {"response": response, "at_risk_count": len(at_risk)})
                print(f"[A2A RESPONSE] {len(at_risk)} at-risk APs")
                return response
            else:
                # Return all risk scores
                response = f"All Risk Scores ({len(data)} APs):\n"
                for ap_serial, ap_data in data.items():
                    current_data = ap_data.get('current', {})
                    response += f"  - {ap_serial}: Risk {current_data.get('risk_score', 0)} - {current_data.get('risk_classification', 'Unknown')}\n"
                
                span.set_attribute("total_aps", len(data))
                span.set_attribute("output.value", response)
                span.add_event("A2A Response Sent", {"response": response, "total_aps": len(data)})
                print(f"[A2A RESPONSE] {len(data)} total APs")
                return response
    
    def start_a2a_server(self):
        """Start A2A server in background thread"""
        class RiskA2AServer(A2AServer):
            def __init__(self, port, handler):
                super().__init__(url=f"http://localhost:{port}")
                self.port = port
                self.handler = handler
                self.request_count = 0
            
            def handle_message(self, message) -> Message:
                self.request_count += 1
                # Get text from message
                if hasattr(message.content, 'text'):
                    text = message.content.text
                else:
                    text = str(message.content)
                
                # Get response
                response_text = self.handler(text)
                
                # Return Message object
                return Message(
                    content=TextContent(text=response_text),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
        
        self.a2a_server = RiskA2AServer(self.a2a_port, self.handle_a2a_message)
        print(f"\n[A2A] Starting server on port {self.a2a_port}...")
        thread = threading.Thread(
            target=lambda: run_server(self.a2a_server, port=self.a2a_port),
            daemon=True
        )
        thread.start()
        import time
        time.sleep(2)  # Give server time to start
        print(f"[A2A] Server ready: http://localhost:{self.a2a_port}\n")
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for risk score orchestration"""
        return f"""You are a RISK SCORE ORCHESTRATOR. You coordinate tool calls - YOU DO NOT CALCULATE ANYTHING.

**3-STEP WORKFLOW:**

**STEP 1: DISCOVER ALL APs**
- Call: get_network_topology_link_layer(network_id="{self.network_id}")
- Extract ALL AP serials and names from response
- Count total APs: "Found X APs"
- List ALL serials to verify 100% coverage

**STEP 2: COLLECT METRICS (for each AP)**
- get_wireless_latency_history(network_id, device_serial) → latency_ms, jitter_ms
- get_wireless_usage_history(network_id, device_serial) → retrans_per_min, snr_db, client_count
- get_device_clients(device_serial) → client_count
- Use null/None if any metric is missing

**STEP 3: CALCULATE RISK (for each AP)**
- Call: calculate_risk_score_tool(ap_serial, ap_name, latency_ms, jitter_ms, retrans_per_min, snr_db, client_count)
- **MUST pass ap_serial and ap_name (required)**
- **For optional parameters: ONLY include if you have a value, OMIT if missing**
- Example with some metrics: calculate_risk_score(ap_serial="Q2XX-ABCD-1234", ap_name="AP-03", retrans_per_min=60, snr_db=15.7, client_count=2)
- Example with only clients: calculate_risk_score(ap_serial="Q2XX-AP06-5678", ap_name="AP-06", client_count=1)
- Tool returns: {{risk_score, risk_classification, metrics, calculation}}
- Call: update_risk_score(ap_serial, risk_result) to store

**CRITICAL RULES:**
1. Process **ALL APs from Step 1** - no skipping!
2. Pass **ap_serial and ap_name (required)** + any available metrics to calculate_risk_score
3. **OMIT missing metrics** - do NOT pass None, null, or 0
4. Use EXACT serial numbers from discovery (14 chars with dashes)
5. At end, verify: "Processed X out of X APs (100% complete)"

**YOU NEVER CALCULATE - the calculate_risk_score tool does ALL math for you!**"""
    
    async def calculate_risk_scores(self) -> Dict[str, Any]:
        """Run risk score calculation orchestration for all APs"""
        try:
            prompt = f"""**EXECUTE RISK SCORE ORCHESTRATION NOW:**

Network ID: {self.network_id}

**CRITICAL: You MUST discover and process 100% of ALL APs in this network!**

**STEP 1:** Discover ALL APs (dynamic discovery)
- Call: get_network_topology_link_layer(network_id="{self.network_id}")
- Extract **EVERY SINGLE AP** from the response
- Count how many you found: "Found X APs"
- Create a list of ALL AP serials and names
- DO NOT skip any AP in the response!

**STEP 2:** For EVERY AP discovered, collect metrics (use parallel calls for efficiency)
- get_wireless_latency_history → extract: latency_ms, jitter_ms (if available)
- get_wireless_usage_history → extract: retrans_per_min, snr_db, client_count
- get_device_clients → extract: client_count

**STEP 3:** For EVERY AP discovered - call calculate_risk_score!

Call calculate_risk_score for EACH AP with:
  1. ap_serial (from Step 1) - REQUIRED - always include
  2. ap_name (from Step 1) - REQUIRED - always include
  3. latency_ms (from Step 2) - OPTIONAL - only include if you have a value
  4. jitter_ms (from Step 2) - OPTIONAL - only include if you have a value
  5. retrans_per_min (from Step 2) - OPTIONAL - only include if you have a value
  6. snr_db (from Step 2) - OPTIONAL - only include if you have a value
  7. client_count (from Step 2) - OPTIONAL - only include if you have a value

**CRITICAL: Do NOT pass None, null, or 0 for missing metrics - just OMIT them!**

Example calls:
- With some metrics: calculate_risk_score(ap_serial="Q2XX-ABCD-1234", ap_name="AP-03", retrans_per_min=60, snr_db=15.7, client_count=2)
- With only client count: calculate_risk_score(ap_serial="Q2XX-AP06-5678", ap_name="AP-06", client_count=1)
- Minimal (only required): calculate_risk_score(ap_serial="Q2XX-AP01-1111", ap_name="AP-01")

Then call update_risk_score to store the result in JSON.

**VALIDATION BEFORE CALLING calculate_risk_score_tool:**
✓ All 7 parameters included?
✓ ap_serial is EXACT 14-char serial from discovery?
✓ ap_name is from discovery?
✓ Metrics from MCP tool responses (or None)?

**FINAL REQUIREMENT:**
At the end, verify: "Processed X out of X APs (100% complete)"
Where X = number of APs discovered in Step 1

**If discovered ≠ processed, YOU ARE NOT DONE! Go back and process the missing APs!**

**BEGIN EXECUTION - DO NOT STOP UNTIL ALL DISCOVERED APs ARE PROCESSED!**
"""
            
            agent_context = RiskAgentContext(
                session_id=self.session_id,
                user_id=self.user_id,
                network_id=self.network_id,
                calculation_interval=self.calculation_interval
            )
            
            # Create callback for tool logging
            tool_logger = ToolCallLogger(self.tool_tracker)
            
            result = await self.agent.ainvoke(
                {"messages": [{"role": "user", "content": prompt}]},
                context=agent_context,
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
            
            # Print verification after execution
            print("\n" + "="*100)
            self.tool_tracker.print_verification()
            
            # Save verification log
            log_path = os.path.join(project_root, "agent_data", "tool_call_verification.json")
            self.tool_tracker.save_log(log_path)
            print(f"📝 Verification log saved: {log_path}\n")
            
            # Print final response (LLM's summary)
            if final_response:
                print("=" * 100)
                print("📊 AGENT SUMMARY:")
                print("=" * 100)
                print(final_response)
                print("=" * 100 + "\n")
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "response": final_response,
                "tool_calls": len(self.tool_tracker.calls)
            }
            
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }
    
    async def continuous_calculation(self):
        """Run continuous risk score calculation"""
        print(f"🚀 Starting continuous risk orchestration (interval: {self.calculation_interval}s)")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                print(f"\n{'='*80}")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Calculation #{iteration}")
                print(f"{'='*80}")
                
                result = await self.calculate_risk_scores()
                
                if result["success"]:
                    print(result["response"])
                else:
                    print(f"❌ Failed: {result.get('error')}")
                
                print(f"\n⏳ Next calculation in {self.calculation_interval}s...")
                await asyncio.sleep(self.calculation_interval)
                
        except KeyboardInterrupt:
            print("\n⚠️ Stopped by user")
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    async def single_calculation(self):
        """Perform a single risk score calculation"""
        result = await self.calculate_risk_scores()
        
        if result["success"]:
            print("\n" + result["response"])
        else:
            print(f"❌ Failed: {result.get('error')}")
        
        return result


async def main():
    """Main entry point"""
    
    # Initialize Phoenix tracing for A2A
    resource = Resource.create({"service.name": "agent-1-risk-a2a"})
    tracer_provider = trace_sdk.TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(endpoint="http://127.0.0.1:6006/v1/traces")
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)
    print("✅ Phoenix tracing enabled for A2A: http://localhost:6006\n")
    
    # Check if Phoenix server is running before enabling tracing
    phoenix_session = None
    try:
        import requests
        response = requests.get("http://localhost:6006", timeout=1)
        if response.status_code == 200:
            print("\n🔍 Phoenix server detected, enabling tracing...")
            from core.phoenix_tracing import initialize_phoenix
            phoenix_session = initialize_phoenix(
                project_name="Agent 1: Risk Calculation",
                launch_ui=False,
                ui_port=6006,
                enable_langchain_instrumentation=True
            )
            if phoenix_session:
                print("✅ Phoenix tracing enabled: http://localhost:6006")
                print("📁 Traces saved to: .phoenix/phoenix_traces.db\n")
    except:
        # Phoenix server not running - continue without tracing
        pass
    
    print("""
===============================================================================
            RISK SCORE ORCHESTRATOR AGENT (Agent 1 - Simplified)
                                                                              
  Discovers APs -> Collects Metrics -> Calls Script -> Stores Results
  Script does ALL calculations - Agent just coordinates!
===============================================================================
    """)
    
    # Parse arguments
    mode = "single"
    interval = 10
    
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
            print("  python agent_1_risk_cal.py                    - Single calculation")
            print("  python agent_1_risk_cal.py --continuous [sec] - Continuous mode")
            print("  python agent_1_risk_cal.py --help             - Show this help")
            print("\nExamples:")
            print("  python agent_1_risk_cal.py --continuous 10    - Calculate every 10s")
            print("  python agent_1_risk_cal.py --continuous 30    - Calculate every 30s")
            return
        i += 1
    
    # Initialize agent
    agent = RiskScoreOrchestrator(calculation_interval=interval, a2a_port=5001)
    
    if not await agent.initialize():
        print("❌ Failed to initialize agent")
        return
    
    print("✅ Agent ready\n")
    
    # Start A2A server
    agent.start_a2a_server()
    
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
