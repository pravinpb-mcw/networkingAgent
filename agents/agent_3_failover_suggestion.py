"""
Agent 3: Failover Suggestion Agent
Reads data from Agent 1 (risk scores) and Agent 2 (nearest APs)
Generates failover suggestions with professional analysis

GLM-4.5 Role: Analysis and reasoning based on data
- Read policy, risk scores, and nearest APs
- Analyze data and provide recommendations
- Show professional tables with actual metrics
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.chat_models import init_chat_model
from langchain_core.callbacks import BaseCallbackHandler

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class RealtimeToolLogger:
    """Logger that shows tool calls immediately"""
    
    def __init__(self):
        self.call_count = 0
    
    def log_call(self, tool_name: str):
        """Log tool call in real-time"""
        self.call_count += 1
        print(f"  [{self.call_count}] Calling: {tool_name}")


# Create global logger
tool_logger = RealtimeToolLogger()


class ToolCallbackHandler(BaseCallbackHandler):
    """Callback to show tool calls in real-time"""
    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get("name", "unknown")
        tool_logger.log_call(tool_name)


async def main():
    """Agent 3: Failover Suggestion Agent"""
    
    print("="*80)
    print("🚨 AGENT 3: FAILOVER SUGGESTION AGENT")
    print("="*80)
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    print(f"🤖 Model: GLM-4.5")
    print("="*80)
    
    # Initialize GLM-4.5 model
    print("\n🔌 Initializing GLM-4.5...")
    model = init_chat_model(
        "claude-sonnet-4-20250514",
        model_provider="anthropic",
        base_url="https://api.z.ai/api/anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY", "60b19768f0334766a3e3259590b14460.QTFX9bVQYgALL0Mj"),
        temperature=0
    )
    
    # Initialize MCP client
    print("🔌 Connecting to MCP server...")
    server_script_path = str(project_root / "server" / "meraki_server.py")
    
    mcp_client = MultiServerMCPClient({
        "cisco-meraki-observability": {
            "transport": "stdio",
            "command": "python",
            "args": [server_script_path],
            "env": {
                "TIMESPAN": "7200",
                "BASE_URL": "https://api.meraki.com/api/v1",
                "MOCK_BASE_URL": "http://127.0.0.1:5000",
                "PRODUCT_TYPE": "appliance"
            }
        }
    })
    
    try:
        # Get available tools
        tools = await mcp_client.get_tools()
        print(f"✅ Connected - {len(tools)} tools available\n")
        
        print("="*80)
        print("🔧 TOOL CALLS (Real-time)")
        print("="*80)
        
        # System prompt
        system_prompt = """You are Agent 3: Failover Suggestion Agent.

WORKFLOW:
1. Call read_network_policy - get failover threshold
2. Call read_risk_scores with min_threshold - find failing APs
3. Call read_nearest_aps for each failing AP - get candidates

OUTPUT FORMAT (Use actual data from tool responses):

## PREDICTIVE ANALYSIS COMPLETE - [AP_NAME]

### RISK CLASSIFICATION: [Category from data]
### RISK SCORE: [Actual score]/100

### CLIENT IMPACT:
CONNECTED CLIENTS: [Number from data]
- [Client details if available]

### RANKED FAILOVER CANDIDATES:

TOP RECOMMENDATION: [AP Serial] ([AP Name])
- Score: [Composite score from data]/100
- Distance: [Actual meters]m
- RSSI: [Actual dBm]dBm  
- Current Load: [Client count] clients
- Same Floor: [Yes/No]
- Risk Score: [Risk score of candidate AP]

SECONDARY: [2nd best AP with metrics]

TERTIARY: [3rd best AP with metrics]

### IMMEDIATE ACTION REQUIRED:
EXECUTION PLAN:
1. Switch clients from [failing AP] to [recommended AP]
2. Monitor load increase
3. Fallback plan if needed

Use ONLY actual numbers from tool responses. No invented data."""

        # Create agent
        agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=system_prompt
        )
        
        # Execute agent
        user_query = "Analyze network for failover recommendations. Use tables and actual data."
        
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": user_query}]},
            config={"recursion_limit": 50, "callbacks": [ToolCallbackHandler()]}
        )
        
        print("="*80)
        
        # Extract final message
        messages = result.get("messages", [])
        if messages:
            final_message = messages[-1]
            
            print(f"\n{'='*80}")
            print("📊 FAILOVER ANALYSIS REPORT")
            print(f"{'='*80}\n")
            print(final_message.content)
            print(f"\n{'='*80}")
        
        print(f"\n✅ Analysis complete ({tool_logger.call_count} tool calls)\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
